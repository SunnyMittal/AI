package middleware

import (
	"context"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/mcp/go-calculator/internal/logger"
	"go.uber.org/zap"
)

// RequestIDKey is the context key for request ID
type contextKey string

const RequestIDKey contextKey = "request_id"

// Logging middleware logs HTTP requests
func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a response writer wrapper to capture status code
		wrapped := &responseWriter{
			ResponseWriter: w,
			statusCode:     http.StatusOK,
		}

		// Log request
		logger.Info("incoming request",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.String("remote_addr", r.RemoteAddr),
			zap.String("user_agent", r.UserAgent()),
		)

		// Call next handler
		next.ServeHTTP(wrapped, r)

		// Log response
		duration := time.Since(start)
		logger.Info("request completed",
			zap.String("method", r.Method),
			zap.String("path", r.URL.Path),
			zap.Int("status", wrapped.statusCode),
			zap.Duration("duration", duration),
			zap.Int64("duration_ms", duration.Milliseconds()),
		)
	})
}

// Recovery middleware recovers from panics
func Recovery(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				logger.Error("panic recovered",
					zap.Any("error", err),
					zap.String("method", r.Method),
					zap.String("path", r.URL.Path),
				)

				http.Error(w, "Internal server error", http.StatusInternalServerError)
			}
		}()

		next.ServeHTTP(w, r)
	})
}

// Timeout middleware adds a timeout to requests
// Note: This middleware should NOT be used for SSE/streaming endpoints
func Timeout(duration time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip timeout for SSE requests (they are long-lived by design)
			accept := r.Header.Get("Accept")
			if strings.Contains(accept, "text/event-stream") {
				next.ServeHTTP(w, r)
				return
			}

			ctx, cancel := context.WithTimeout(r.Context(), duration)
			defer cancel()

			r = r.WithContext(ctx)

			// Use a timeout-aware response writer to prevent race conditions
			tw := &timeoutWriter{
				ResponseWriter: w,
				mu:             &sync.Mutex{},
			}

			done := make(chan struct{})
			go func() {
				next.ServeHTTP(tw, r)
				close(done)
			}()

			select {
			case <-done:
				// Request completed successfully
			case <-ctx.Done():
				tw.mu.Lock()
				defer tw.mu.Unlock()
				if !tw.wroteHeader {
					tw.timedOut = true
					logger.Warn("request timeout",
						zap.String("method", r.Method),
						zap.String("path", r.URL.Path),
						zap.Duration("timeout", duration),
					)
					w.WriteHeader(http.StatusGatewayTimeout)
					w.Write([]byte("Request timeout"))
				}
			}
		})
	}
}

// timeoutWriter wraps ResponseWriter to handle timeout race conditions
type timeoutWriter struct {
	http.ResponseWriter
	mu          *sync.Mutex
	wroteHeader bool
	timedOut    bool
}

func (tw *timeoutWriter) WriteHeader(code int) {
	tw.mu.Lock()
	defer tw.mu.Unlock()
	if tw.timedOut || tw.wroteHeader {
		return
	}
	tw.wroteHeader = true
	tw.ResponseWriter.WriteHeader(code)
}

func (tw *timeoutWriter) Write(b []byte) (int, error) {
	tw.mu.Lock()
	defer tw.mu.Unlock()
	if tw.timedOut {
		return 0, context.DeadlineExceeded
	}
	if !tw.wroteHeader {
		tw.wroteHeader = true
		tw.ResponseWriter.WriteHeader(http.StatusOK)
	}
	return tw.ResponseWriter.Write(b)
}

func (tw *timeoutWriter) Flush() {
	tw.mu.Lock()
	defer tw.mu.Unlock()
	if tw.timedOut {
		return
	}
	if f, ok := tw.ResponseWriter.(http.Flusher); ok {
		f.Flush()
	}
}

// RateLimiter provides simple in-memory rate limiting
func RateLimiter(requestsPerSecond int) func(http.Handler) http.Handler {
	type client struct {
		lastSeen  time.Time
		requests  int
		resetTime time.Time
	}

	var mu sync.RWMutex
	clients := make(map[string]*client)
	ticker := time.NewTicker(time.Minute)

	// Cleanup old entries periodically
	go func() {
		for range ticker.C {
			mu.Lock()
			cutoff := time.Now().Add(-5 * time.Minute)
			for ip, c := range clients {
				if c.lastSeen.Before(cutoff) {
					delete(clients, ip)
				}
			}
			mu.Unlock()
		}
	}()

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ip := r.RemoteAddr
			now := time.Now()

			mu.Lock()
			c, exists := clients[ip]
			if !exists {
				clients[ip] = &client{
					lastSeen:  now,
					requests:  1,
					resetTime: now.Add(time.Second),
				}
				mu.Unlock()
				next.ServeHTTP(w, r)
				return
			}

			c.lastSeen = now

			// Reset counter if time window has passed
			if now.After(c.resetTime) {
				c.requests = 1
				c.resetTime = now.Add(time.Second)
				mu.Unlock()
				next.ServeHTTP(w, r)
				return
			}

			// Check rate limit
			if c.requests >= requestsPerSecond {
				mu.Unlock()
				logger.Warn("rate limit exceeded",
					zap.String("ip", ip),
					zap.Int("requests", c.requests),
				)
				http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
				return
			}

			c.requests++
			mu.Unlock()
			next.ServeHTTP(w, r)
		})
	}
}

// SecurityHeaders adds security headers to responses
func SecurityHeaders(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Prevent clickjacking
		w.Header().Set("X-Frame-Options", "DENY")

		// Prevent MIME type sniffing
		w.Header().Set("X-Content-Type-Options", "nosniff")

		// Enable XSS protection
		w.Header().Set("X-XSS-Protection", "1; mode=block")

		// Referrer policy
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")

		// Content Security Policy
		w.Header().Set("Content-Security-Policy", "default-src 'self'")

		next.ServeHTTP(w, r)
	})
}

// RequestValidator validates request size and content type
func RequestValidator(maxBodySize int64) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check content length
			if r.ContentLength > maxBodySize {
				logger.Warn("request body too large",
					zap.Int64("content_length", r.ContentLength),
					zap.Int64("max_size", maxBodySize),
				)
				http.Error(w, "Request body too large", http.StatusRequestEntityTooLarge)
				return
			}

			// Validate content type for POST requests
			if r.Method == http.MethodPost {
				contentType := r.Header.Get("Content-Type")
				if contentType != "application/json" && contentType != "application/json; charset=utf-8" {
					logger.Warn("invalid content type",
						zap.String("content_type", contentType),
					)
					http.Error(w, "Content-Type must be application/json", http.StatusUnsupportedMediaType)
					return
				}
			}

			next.ServeHTTP(w, r)
		})
	}
}

// Chain chains multiple middleware functions
func Chain(h http.Handler, middlewares ...func(http.Handler) http.Handler) http.Handler {
	for i := len(middlewares) - 1; i >= 0; i-- {
		h = middlewares[i](h)
	}
	return h
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Flush implements http.Flusher interface for SSE support
func (rw *responseWriter) Flush() {
	if f, ok := rw.ResponseWriter.(http.Flusher); ok {
		f.Flush()
	}
}

package middleware

import (
	"context"
	"net/http"
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
func Timeout(duration time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx, cancel := context.WithTimeout(r.Context(), duration)
			defer cancel()

			r = r.WithContext(ctx)

			done := make(chan struct{})
			go func() {
				next.ServeHTTP(w, r)
				close(done)
			}()

			select {
			case <-done:
				// Request completed successfully
			case <-ctx.Done():
				if ctx.Err() == context.DeadlineExceeded {
					logger.Warn("request timeout",
						zap.String("method", r.Method),
						zap.String("path", r.URL.Path),
						zap.Duration("timeout", duration),
					)
					http.Error(w, "Request timeout", http.StatusGatewayTimeout)
				}
			}
		})
	}
}

// RateLimiter provides simple in-memory rate limiting
func RateLimiter(requestsPerSecond int) func(http.Handler) http.Handler {
	type client struct {
		lastSeen  time.Time
		requests  int
		resetTime time.Time
	}

	clients := make(map[string]*client)
	ticker := time.NewTicker(time.Minute)

	// Cleanup old entries periodically
	go func() {
		for range ticker.C {
			cutoff := time.Now().Add(-5 * time.Minute)
			for ip, c := range clients {
				if c.lastSeen.Before(cutoff) {
					delete(clients, ip)
				}
			}
		}
	}()

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ip := r.RemoteAddr
			now := time.Now()

			c, exists := clients[ip]
			if !exists {
				clients[ip] = &client{
					lastSeen:  now,
					requests:  1,
					resetTime: now.Add(time.Second),
				}
				next.ServeHTTP(w, r)
				return
			}

			c.lastSeen = now

			// Reset counter if time window has passed
			if now.After(c.resetTime) {
				c.requests = 1
				c.resetTime = now.Add(time.Second)
				next.ServeHTTP(w, r)
				return
			}

			// Check rate limit
			if c.requests >= requestsPerSecond {
				logger.Warn("rate limit exceeded",
					zap.String("ip", ip),
					zap.Int("requests", c.requests),
				)
				http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
				return
			}

			c.requests++
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

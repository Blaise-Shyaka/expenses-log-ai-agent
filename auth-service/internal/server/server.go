package server

import (
	"net/http"

	"github.com/blaise/momo-expenses/auth-service/internal/handlers"
	"github.com/blaise/momo-expenses/auth-service/internal/keys"
	"github.com/blaise/momo-expenses/auth-service/internal/store"
	"github.com/blaise/momo-expenses/auth-service/internal/tokens"
)

func New(st store.Store, km *keys.Manager, minter *tokens.Minter) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", handlers.Health)
	mux.HandleFunc("GET /.well-known/jwks.json", handlers.JWKS(km.PublicJWKS()))
	mux.HandleFunc("POST /register", handlers.Register(st))
	mux.HandleFunc("POST /login", handlers.Login(st, minter))
	mux.HandleFunc("POST /oauth/token", handlers.Token(st, minter))

	return mux
}

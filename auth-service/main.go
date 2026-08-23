package main

import (
	"log"
	"net/http"
	"os"

	"github.com/blaise/momo-expenses/auth-service/internal/keys"
	"github.com/blaise/momo-expenses/auth-service/internal/seed"
	"github.com/blaise/momo-expenses/auth-service/internal/server"
	"github.com/blaise/momo-expenses/auth-service/internal/store"
	"github.com/blaise/momo-expenses/auth-service/internal/tokens"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}

	keyPath := os.Getenv("SIGNING_KEY_PATH")
	if keyPath == "" {
		keyPath = "signing.key"
	}
	keyPEM := os.Getenv("SIGNING_KEY_PEM")

	issuer := os.Getenv("ISSUER_URL")
	if issuer == "" {
		issuer = "http://localhost:8001"
	}

	dbURL := os.Getenv("DATABASE_URL")

	var st store.Store
	if dbURL != "" {
		pgStore, err := store.NewPostgresStore(dbURL)
		if err != nil {
			log.Fatalf("connect to postgres: %v", err)
		}
		defer pgStore.Close()
		if err := pgStore.Migrate(); err != nil {
			log.Fatalf("run migrations: %v", err)
		}
		st = pgStore
	} else {
		log.Println("DATABASE_URL not set; using in-memory store (data will not persist)")
		st = store.NewMemoryStore()
	}

	var km *keys.Manager
	var err error
	if keyPEM != "" {
		km, err = keys.LoadFromPEM([]byte(keyPEM))
		if err != nil {
			log.Fatalf("load signing key from SIGNING_KEY_PEM: %v", err)
		}
	} else {
		km, err = keys.LoadOrGenerate(keyPath)
		if err != nil {
			log.Fatalf("load/generate signing key: %v", err)
		}
	}

	minter := tokens.NewMinter(km.PrivateKey(), km.KID(), issuer)

	svcAgentSecret := os.Getenv("SVC_AGENT_SECRET")
	svcMCPSecret := os.Getenv("SVC_MCP_SECRET")
	if svcAgentSecret != "" && svcMCPSecret != "" {
		clients := []seed.MachineClientConfig{
			{ClientID: "svc-agent", Secret: svcAgentSecret, Audience: "expenses-mcp", Scopes: "mcp:call act-on-behalf"},
			{ClientID: "svc-mcp", Secret: svcMCPSecret, Audience: "expenses-api", Scopes: "expenses:read expenses:write act-on-behalf"},
		}
		if err := seed.MachineClients(st, clients); err != nil {
			log.Fatalf("seed machine clients: %v", err)
		}
		log.Println("machine clients seeded")
	}

	if os.Getenv("SEED_DEV_USER") == "true" {
		const devUserID = "00000000-0000-0000-0000-000000000001"
		const devEmail = "dev@localhost"
		const devPassword = "dev"
		if err := seed.DevUser(st, devUserID, devEmail, devPassword); err != nil {
			log.Fatalf("seed dev user: %v", err)
		}
		log.Println("dev user seeded")
	}

	handler := server.New(st, km, minter)

	addr := ":" + port
	log.Printf("auth-service listening on %s", addr)
	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("serve: %v", err)
	}
}

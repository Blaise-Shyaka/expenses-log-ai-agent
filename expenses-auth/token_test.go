package main_test

import (
	"encoding/base64"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/lestrrat-go/jwx/v2/jwa"
	"github.com/lestrrat-go/jwx/v2/jwk"
	"github.com/lestrrat-go/jwx/v2/jwt"

	"github.com/blaise/momo-expenses/expenses-auth/internal/keys"
	"github.com/blaise/momo-expenses/expenses-auth/internal/seed"
	"github.com/blaise/momo-expenses/expenses-auth/internal/server"
	"github.com/blaise/momo-expenses/expenses-auth/internal/store"
	"github.com/blaise/momo-expenses/expenses-auth/internal/tokens"
)

type testEnv struct {
	srv    *httptest.Server
	st     *store.MemoryStore
	km     *keys.Manager
	minter *tokens.Minter
}

func newTestEnv(t *testing.T) *testEnv {
	t.Helper()
	tmp, err := os.CreateTemp(t.TempDir(), "signing-*.key")
	if err != nil {
		t.Fatalf("create temp key file: %v", err)
	}
	tmp.Close()
	os.Remove(tmp.Name())

	km, err := keys.LoadOrGenerate(tmp.Name())
	if err != nil {
		t.Fatalf("load/generate key: %v", err)
	}

	st := store.NewMemoryStore()
	minter := tokens.NewMinter(km.PrivateKey(), km.KID(), "http://localhost:8001")
	h := server.New(st, km, minter)
	return &testEnv{
		srv:    httptest.NewServer(h),
		st:     st,
		km:     km,
		minter: minter,
	}
}

func postForm(t *testing.T, srv *httptest.Server, path string, form url.Values) *http.Response {
	t.Helper()
	resp, err := http.PostForm(srv.URL+path, form)
	if err != nil {
		t.Fatalf("POST form %s: %v", path, err)
	}
	return resp
}

func seedTestClient(t *testing.T, st *store.MemoryStore, clientID, secret, audience, scopes string) {
	t.Helper()
	err := seed.MachineClients(st, []seed.MachineClientConfig{
		{ClientID: clientID, Secret: secret, Audience: audience, Scopes: scopes},
	})
	if err != nil {
		t.Fatalf("seed machine client %q: %v", clientID, err)
	}
}

func jwtHasKID(t *testing.T, rawToken string) bool {
	t.Helper()
	parts := strings.Split(rawToken, ".")
	if len(parts) != 3 {
		t.Fatalf("not a JWT: %q", rawToken)
	}
	headerJSON, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		t.Fatalf("decode JWT header: %v", err)
	}
	var header map[string]any
	if err := json.Unmarshal(headerJSON, &header); err != nil {
		t.Fatalf("unmarshal JWT header: %v", err)
	}
	kid, _ := header["kid"].(string)
	return kid != ""
}

func parseJWT(t *testing.T, km *keys.Manager, rawToken string) jwt.Token {
	t.Helper()
	privJWK, err := jwk.FromRaw(km.PrivateKey())
	if err != nil {
		t.Fatalf("build JWK: %v", err)
	}
	if err := privJWK.Set(jwk.KeyIDKey, km.KID()); err != nil {
		t.Fatalf("set kid: %v", err)
	}
	if err := privJWK.Set(jwk.AlgorithmKey, jwa.RS256); err != nil {
		t.Fatalf("set alg: %v", err)
	}
	parsed, err := jwt.Parse([]byte(rawToken), jwt.WithKey(jwa.RS256, privJWK), jwt.WithValidate(true))
	if err != nil {
		t.Fatalf("parse JWT: %v", err)
	}
	return parsed
}

func TestClientCredentials_Success(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	seedTestClient(t, env.st, "svc-agent", "supersecret", "expenses-mcp", "mcp:call act-on-behalf")

	resp := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"client_credentials"},
		"client_id":     {"svc-agent"},
		"client_secret": {"supersecret"},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("client_credentials: want 200, got %d: %s", resp.StatusCode, body)
	}

	var result map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		t.Fatalf("decode response: %v", err)
	}

	accessToken, ok := result["access_token"].(string)
	if !ok || accessToken == "" {
		t.Fatal("access_token must be present and non-empty")
	}
	if result["token_type"] != "Bearer" {
		t.Errorf("token_type: want Bearer, got %v", result["token_type"])
	}
	if _, ok := result["expires_in"].(float64); !ok {
		t.Error("expires_in must be present")
	}
	if _, ok := result["refresh_token"]; ok {
		t.Error("refresh_token must NOT be present for client_credentials grant")
	}

	parsed := parseJWT(t, env.km, accessToken)

	if parsed.Subject() != "svc-agent" {
		t.Errorf("sub: want svc-agent, got %q", parsed.Subject())
	}
	aud := parsed.Audience()
	if len(aud) == 0 || aud[0] != "expenses-mcp" {
		t.Errorf("aud: want expenses-mcp, got %v", aud)
	}
	scope, _ := parsed.Get("scope")
	if scope != "mcp:call act-on-behalf" {
		t.Errorf("scope: want \"mcp:call act-on-behalf\", got %v", scope)
	}
	tokenType, _ := parsed.Get("token_type")
	if tokenType != "service" {
		t.Errorf("token_type claim: want service, got %v", tokenType)
	}
	if !jwtHasKID(t, accessToken) {
		t.Error("kid must be present in JWT header")
	}
}

func TestClientCredentials_BasicAuth(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	seedTestClient(t, env.st, "svc-mcp", "anothersecret", "expenses-api", "expenses:read expenses:write")

	req, _ := http.NewRequest(http.MethodPost, env.srv.URL+"/oauth/token", strings.NewReader("grant_type=client_credentials"))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.SetBasicAuth("svc-mcp", "anothersecret")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("POST: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("basic auth: want 200, got %d: %s", resp.StatusCode, body)
	}
}

func TestClientCredentials_WrongSecret(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	seedTestClient(t, env.st, "svc-agent", "correctsecret", "expenses-mcp", "mcp:call")

	resp := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"client_credentials"},
		"client_id":     {"svc-agent"},
		"client_secret": {"wrongsecret"},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("wrong secret: want 401, got %d", resp.StatusCode)
	}
}

func TestClientCredentials_UnknownClient(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	resp := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"client_credentials"},
		"client_id":     {"ghost-client"},
		"client_secret": {"anything"},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("unknown client: want 401, got %d", resp.StatusCode)
	}
}

func TestRefreshToken_Success(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	postJSON(t, env.srv, "/register", map[string]string{
		"email": "refresh@example.com", "password": "pass", "first_name": "R", "last_name": "T",
	}).Body.Close()

	loginResp := postJSON(t, env.srv, "/login", map[string]string{
		"email": "refresh@example.com", "password": "pass",
	})
	defer loginResp.Body.Close()

	var loginResult map[string]any
	json.NewDecoder(loginResp.Body).Decode(&loginResult)
	oldRefreshToken := loginResult["refresh_token"].(string)

	resp := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {oldRefreshToken},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("refresh_token: want 200, got %d: %s", resp.StatusCode, body)
	}

	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)

	newAccessToken, ok := result["access_token"].(string)
	if !ok || newAccessToken == "" {
		t.Error("access_token must be present")
	}
	newRefreshToken, ok := result["refresh_token"].(string)
	if !ok || newRefreshToken == "" {
		t.Error("refresh_token must be present after rotation")
	}
	if newRefreshToken == oldRefreshToken {
		t.Error("rotated refresh_token must differ from the old one")
	}

	parsed := parseJWT(t, env.km, newAccessToken)
	tokenType, _ := parsed.Get("token_type")
	if tokenType != "user" {
		t.Errorf("token_type: want user, got %v", tokenType)
	}
}

func TestRefreshToken_Rotation_OldTokenReturns401(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	postJSON(t, env.srv, "/register", map[string]string{
		"email": "rotate@example.com", "password": "pass", "first_name": "R", "last_name": "T",
	}).Body.Close()

	loginResp := postJSON(t, env.srv, "/login", map[string]string{
		"email": "rotate@example.com", "password": "pass",
	})
	defer loginResp.Body.Close()

	var loginResult map[string]any
	json.NewDecoder(loginResp.Body).Decode(&loginResult)
	oldRT := loginResult["refresh_token"].(string)

	postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {oldRT},
	}).Body.Close()

	resp2 := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {oldRT},
	})
	defer resp2.Body.Close()

	if resp2.StatusCode != http.StatusUnauthorized {
		t.Errorf("reused refresh token: want 401, got %d", resp2.StatusCode)
	}
}

func TestRefreshToken_GarbageToken_Returns401(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	resp := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {"this-is-garbage-and-does-not-exist"},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("garbage token: want 401, got %d", resp.StatusCode)
	}
}

func TestToken_UnknownGrantType_Returns400(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	resp := postForm(t, env.srv, "/oauth/token", url.Values{
		"grant_type": {"authorization_code"},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("unknown grant_type: want 400, got %d", resp.StatusCode)
	}
}

func TestToken_MissingGrantType_Returns400(t *testing.T) {
	env := newTestEnv(t)
	defer env.srv.Close()

	resp := postForm(t, env.srv, "/oauth/token", url.Values{})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("missing grant_type: want 400, got %d", resp.StatusCode)
	}
}

func TestSeed_MachineClients_Idempotent(t *testing.T) {
	st := store.NewMemoryStore()

	clients := []seed.MachineClientConfig{
		{ClientID: "svc-agent", Secret: "s1", Audience: "expenses-mcp", Scopes: "mcp:call act-on-behalf"},
		{ClientID: "svc-mcp", Secret: "s2", Audience: "expenses-api", Scopes: "expenses:read expenses:write act-on-behalf"},
	}

	if err := seed.MachineClients(st, clients); err != nil {
		t.Fatalf("first seed: %v", err)
	}
	if err := seed.MachineClients(st, clients); err != nil {
		t.Fatalf("second seed (idempotent): %v", err)
	}

	c1, err := st.GetMachineClientByID("svc-agent")
	if err != nil {
		t.Fatalf("get svc-agent: %v", err)
	}
	if c1.Audience != "expenses-mcp" {
		t.Errorf("svc-agent audience: want expenses-mcp, got %q", c1.Audience)
	}

	c2, err := st.GetMachineClientByID("svc-mcp")
	if err != nil {
		t.Fatalf("get svc-mcp: %v", err)
	}
	if c2.Audience != "expenses-api" {
		t.Errorf("svc-mcp audience: want expenses-api, got %q", c2.Audience)
	}
}

func TestSeed_DevUser_OnlyWhenFlagSet(t *testing.T) {
	st := store.NewMemoryStore()
	const devUserID = "00000000-0000-0000-0000-000000000001"

	_, err := st.GetUserByID(devUserID)
	if err == nil {
		t.Fatal("dev user should not exist before seeding")
	}

	if err := seed.DevUser(st, devUserID, "dev@localhost", "dev"); err != nil {
		t.Fatalf("seed dev user: %v", err)
	}

	u, err := st.GetUserByID(devUserID)
	if err != nil {
		t.Fatalf("get dev user: %v", err)
	}
	if u.ID != devUserID {
		t.Errorf("dev user ID: want %q, got %q", devUserID, u.ID)
	}

	if err := seed.DevUser(st, devUserID, "dev@localhost", "dev"); err != nil {
		t.Fatalf("second seed (idempotent): %v", err)
	}
}

func TestRefreshToken_ExpiredToken_Returns401(t *testing.T) {
	st := store.NewMemoryStore()

	tmp, _ := os.CreateTemp(t.TempDir(), "*.key")
	tmp.Close()
	os.Remove(tmp.Name())
	km, _ := keys.LoadOrGenerate(tmp.Name())
	minter := tokens.NewMinter(km.PrivateKey(), km.KID(), "http://localhost:8001")
	srv := httptest.NewServer(server.New(st, km, minter))
	defer srv.Close()

	rawRT, hashRT, _ := tokens.GenerateRefreshToken()
	expiredToken := store.RefreshToken{
		TokenHash: hashRT,
		UserID:    "some-user",
		ExpiresAt: time.Now().UTC().Add(-time.Hour),
	}
	st.CreateRefreshToken(expiredToken)

	resp := postForm(t, srv, "/oauth/token", url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {rawRT},
	})
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusUnauthorized {
		t.Errorf("expired token: want 401, got %d", resp.StatusCode)
	}
}

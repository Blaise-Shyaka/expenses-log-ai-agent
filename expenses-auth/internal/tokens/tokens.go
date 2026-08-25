package tokens

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"time"

	"github.com/lestrrat-go/jwx/v2/jwa"
	"github.com/lestrrat-go/jwx/v2/jwk"
	"github.com/lestrrat-go/jwx/v2/jws"
	"github.com/lestrrat-go/jwx/v2/jwt"
)

type Minter struct {
	privateKey *rsa.PrivateKey
	kid        string
	issuer     string
}

func NewMinter(privateKey *rsa.PrivateKey, kid, issuer string) *Minter {
	return &Minter{privateKey: privateKey, kid: kid, issuer: issuer}
}

func (m *Minter) MintUserToken(userID string, ttl time.Duration) (string, error) {
	now := time.Now().UTC()
	tok, err := jwt.NewBuilder().
		Issuer(m.issuer).
		Subject(userID).
		Audience([]string{"expenses-agent"}).
		IssuedAt(now).
		Expiration(now.Add(ttl)).
		Claim("token_type", "user").
		Claim("scope", "chat").
		Build()
	if err != nil {
		return "", fmt.Errorf("build JWT: %w", err)
	}

	headers := jws.NewHeaders()
	if err := headers.Set(jws.AlgorithmKey, jwa.RS256); err != nil {
		return "", fmt.Errorf("set alg header: %w", err)
	}
	if err := headers.Set(jws.KeyIDKey, m.kid); err != nil {
		return "", fmt.Errorf("set kid header: %w", err)
	}

	privJWK, err := jwk.FromRaw(m.privateKey)
	if err != nil {
		return "", fmt.Errorf("build JWK from private key: %w", err)
	}
	if err := privJWK.Set(jwk.KeyIDKey, m.kid); err != nil {
		return "", fmt.Errorf("set kid on JWK: %w", err)
	}

	signed, err := jwt.Sign(tok, jwt.WithKey(jwa.RS256, privJWK, jws.WithProtectedHeaders(headers)))
	if err != nil {
		return "", fmt.Errorf("sign JWT: %w", err)
	}
	return string(signed), nil
}

func GenerateRefreshToken() (raw string, hash string, err error) {
	buf := make([]byte, 32)
	if _, err = rand.Read(buf); err != nil {
		return "", "", fmt.Errorf("generate refresh token bytes: %w", err)
	}
	raw = base64.RawURLEncoding.EncodeToString(buf)
	h := sha256.Sum256([]byte(raw))
	hash = fmt.Sprintf("%x", h[:])
	return raw, hash, nil
}

func HashRefreshToken(raw string) string {
	h := sha256.Sum256([]byte(raw))
	return fmt.Sprintf("%x", h[:])
}

func (m *Minter) MintServiceToken(clientID, audience, scopes string, ttl time.Duration) (string, error) {
	now := time.Now().UTC()
	tok, err := jwt.NewBuilder().
		Issuer(m.issuer).
		Subject(clientID).
		Audience([]string{audience}).
		IssuedAt(now).
		Expiration(now.Add(ttl)).
		Claim("token_type", "service").
		Claim("scope", scopes).
		Build()
	if err != nil {
		return "", fmt.Errorf("build JWT: %w", err)
	}

	headers := jws.NewHeaders()
	if err := headers.Set(jws.AlgorithmKey, jwa.RS256); err != nil {
		return "", fmt.Errorf("set alg header: %w", err)
	}
	if err := headers.Set(jws.KeyIDKey, m.kid); err != nil {
		return "", fmt.Errorf("set kid header: %w", err)
	}

	privJWK, err := jwk.FromRaw(m.privateKey)
	if err != nil {
		return "", fmt.Errorf("build JWK from private key: %w", err)
	}
	if err := privJWK.Set(jwk.KeyIDKey, m.kid); err != nil {
		return "", fmt.Errorf("set kid on JWK: %w", err)
	}

	signed, err := jwt.Sign(tok, jwt.WithKey(jwa.RS256, privJWK, jws.WithProtectedHeaders(headers)))
	if err != nil {
		return "", fmt.Errorf("sign JWT: %w", err)
	}
	return string(signed), nil
}

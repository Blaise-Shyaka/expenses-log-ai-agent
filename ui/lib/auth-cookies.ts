// In the production build, next-auth's cookies are marked Secure and use the
// __Secure-/__Host- names, whatever origin next-auth infers from the request.
// auth.ts and proxy.ts must both use this value: getToken() otherwise guesses
// from NEXTAUTH_URL and looks for a cookie name next-auth never set.
export const SECURE_COOKIES = process.env.NODE_ENV === "production";

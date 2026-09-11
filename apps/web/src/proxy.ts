import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE = "lvfi_admin_session";
const apiUrl = (process.env.LVFI_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function proxy(request: NextRequest) {
  if (!request.cookies.has(SESSION_COOKIE)) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const authenticated = await fetch(`${apiUrl}/auth/session`, {
    cache: "no-store",
    headers: { cookie: request.headers.get("cookie") ?? "" }
  }).then((response) => response.ok).catch(() => false);
  if (authenticated) return NextResponse.next();

  const response = NextResponse.redirect(new URL("/login", request.url));
  response.cookies.delete(SESSION_COOKIE);
  return response;
}

export const config = { matcher: ["/", "/administration/:path*", "/matches/:path*"] };

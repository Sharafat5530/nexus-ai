import { FormEvent, ReactNode, useEffect, useState } from "react";

import {
  api,
  clearAccessToken,
  getAccessToken,
  saveAccessToken,
  SESSION_EXPIRED_EVENT,
} from "@/lib/api";

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string;
}

interface TokenResponse {
  access_token: string;
}

interface AuthGateProps {
  children: ReactNode;
}

export function AuthGate({ children }: AuthGateProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function restoreSession() {
      if (!getAccessToken()) {
        setCheckingSession(false);
        return;
      }

      try {
        const profile = await api<UserProfile>("/auth/me", {
          signal: controller.signal,
        });

        setUser(profile);
      } catch (failure) {
        if (controller.signal.aborted) {
          return;
        }

        setUser(null);
        setError(
          failure instanceof Error
            ? failure.message
            : "Could not restore your session.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setCheckingSession(false);
        }
      }
    }

    function handleExpiredSession() {
      setUser(null);
      setError("Your session expired. Sign in again.");
    }

    window.addEventListener(
      SESSION_EXPIRED_EVENT,
      handleExpiredSession,
    );

    void restoreSession();

    return () => {
      controller.abort();
      window.removeEventListener(
        SESSION_EXPIRED_EVENT,
        handleExpiredSession,
      );
    };
  }, []);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const session = await api<TokenResponse>("/auth/token", {
        method: "POST",
        json: { email: email.trim(), password },
      });

      saveAccessToken(session.access_token);

      const profile = await api<UserProfile>("/auth/me");

      setUser(profile);
      setPassword("");
    } catch (failure) {
      clearAccessToken();
      setError(
        failure instanceof Error
          ? failure.message
          : "Sign-in failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function signOut() {
    clearAccessToken();
    setUser(null);
    setPassword("");
    setError("");
  }

  if (checkingSession) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-canvas">
        <p className="text-sm text-navy-600">Checking your session…</p>
      </main>
    );
  }

  if (user) {
    return (
      <>
        {children}

        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-3 rounded-lg border border-border bg-white px-4 py-2 shadow-sm">
          <span className="text-xs text-navy-600">
            {user.full_name}
          </span>

          <button
            type="button"
            onClick={signOut}
            className="text-xs font-semibold text-teal-700"
          >
            Sign out
          </button>
        </div>
      </>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-canvas p-6">
      <form
        onSubmit={signIn}
        className="w-full max-w-md space-y-5 rounded-xl border border-border bg-white p-8 shadow-sm"
      >
        <div>
          <h1 className="text-2xl font-bold text-navy-900">
            NEXUS AI
          </h1>
          <p className="mt-2 text-sm text-navy-500">
            Sign in to your operator workspace.
          </p>
        </div>

        <label className="block text-sm font-medium text-navy-700">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="username"
            required
            disabled={submitting}
            className="mt-2 block w-full rounded-lg border border-border px-3 py-2"
          />
        </label>

        <label className="block text-sm font-medium text-navy-700">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
            disabled={submitting}
            className="mt-2 block w-full rounded-lg border border-border px-3 py-2"
          />
        </label>

        {error && (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-teal-600 px-4 py-2 font-semibold text-white disabled:opacity-50"
        >
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
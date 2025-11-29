"use client";

import { useState } from "react";

type AuthMode = "login" | "register";

interface AuthFormProps {
  mode: AuthMode;
}

export default function AuthForm({ mode }: AuthFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    const baseURL = "https://replacewithflyappname-production.up.railway.app";

    const endpoint =
      mode === "login"
        ? `${baseURL}/api/auth/login`
        : `${baseURL}/api/auth/register`;

    // 🔥 Backend wymaga name przy rejestracji!
    const payload =
      mode === "login"
        ? { email, password }
        : { email, password, name: name || "Uczeń" };

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || "Błąd serwera");
        setLoading(false);
        return;
      }

      // 🔥 ZAPISYWANIE TOKENA I STUDENT_ID
      localStorage.setItem("token", data.token);
      localStorage.setItem("student_id", String(data.student_id));
      localStorage.setItem("student_name", data.name);

      if (mode === "login") {
        window.location.href = "/chat";
      } else {
        alert("Konto utworzone! Logowanie…");
        window.location.href = "/auth/login";
      }
    } catch (err) {
      alert("Błąd połączenia z backendem");
    }

    setLoading(false);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white p-6 rounded-xl shadow-md space-y-4 w-full max-w-md"
    >
      <h1 className="text-2xl font-semibold text-center">
        {mode === "login" ? "Logowanie" : "Rejestracja"}
      </h1>

      {mode === "register" && (
        <input
          className="border p-2 rounded w-full"
          placeholder="Imię"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      )}

      <input
        className="border p-2 rounded w-full"
        placeholder="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        className="border p-2 rounded w-full"
        placeholder="Hasło"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button
        type="submit"
        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
        disabled={loading}
      >
        {loading
          ? "Przetwarzam..."
          : mode === "login"
          ? "Zaloguj się"
          : "Zarejestruj się"}
      </button>
    </form>
  );
}

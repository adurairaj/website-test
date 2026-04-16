import { useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const featuredProperties = [
  {
    name: "Oceanview Retreat",
    location: "Malibu, California",
    occupancy: "92% Occupancy",
    image:
      "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1400&q=80",
  },
  {
    name: "Urban Loft Collection",
    location: "Austin, Texas",
    occupancy: "88% Occupancy",
    image:
      "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1400&q=80",
  },
  {
    name: "Mountain Escape Villas",
    location: "Aspen, Colorado",
    occupancy: "95% Occupancy",
    image:
      "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1400&q=80",
  },
];

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Welcome to StayPilot. I can help you optimize pricing, guest communication, and occupancy.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const historyForApi = useMemo(
    () => messages.filter((m) => m.role === "user" || m.role === "assistant"),
    [messages]
  );

  async function handleSend(event) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const updated = [...messages, { role: "user", content: trimmed }];
    setMessages(updated);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...historyForApi, { role: "user", content: trimmed }] }),
      });

      if (!response.ok) {
        const details = await response.text();
        throw new Error(details || "Failed to fetch reply");
      }

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setError(err.message || "Unexpected error");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I couldn't reach the server. Please verify the backend connection and try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <div className="background-overlay" />
      <main className="dashboard">
        <section className="hero">
          <p className="eyebrow">Premium Property Operations</p>
          <h1>Manage your Airbnb portfolio with confidence</h1>
          <p className="hero-copy">
            Centralize guest communication, portfolio visibility, and performance tracking in a clean,
            modern command center built for professional property managers.
          </p>
          <div className="hero-metrics">
            <article>
              <span>128</span>
              <p>Active Listings</p>
            </article>
            <article>
              <span>4.93</span>
              <p>Average Rating</p>
            </article>
            <article>
              <span>$287K</span>
              <p>Monthly Revenue</p>
            </article>
          </div>
        </section>

        <section className="content-grid">
          <section className="properties-panel">
            <header>
              <h2>Featured Properties</h2>
              <button type="button">View Portfolio</button>
            </header>
            <div className="property-grid">
              {featuredProperties.map((property) => (
                <article
                  key={property.name}
                  className="property-card"
                  style={{ backgroundImage: `linear-gradient(180deg, rgba(2,6,23,0.2), rgba(2,6,23,0.82)), url(${property.image})` }}
                >
                  <div>
                    <h3>{property.name}</h3>
                    <p>{property.location}</p>
                  </div>
                  <span>{property.occupancy}</span>
                </article>
              ))}
            </div>
          </section>

          <section className="assistant-panel">
            <div className="assistant-heading">
              <h2>StayPilot Assistant</h2>
              <p>Ask for pricing recommendations, guest messaging drafts, and operational insights.</p>
            </div>

            <section className="chat-window" aria-live="polite">
              {messages.map((message, index) => (
                <article key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
                  <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
                  <p>{message.content}</p>
                </article>
              ))}
            </section>

            {error && <p className="error">{error}</p>}

            <form onSubmit={handleSend} className="composer">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask: How should I price my Austin loft next weekend?"
                disabled={loading}
              />
              <button type="submit" disabled={loading || !input.trim()}>
                {loading ? "Sending..." : "Send"}
              </button>
            </form>
          </section>
        </section>
      </main>
    </div>
  );
}

import { useState } from "react";
import {
  Camera,
  CheckCircle2,
  PackageCheck,
  Upload,
  AlertTriangle,
  Clock3,
} from "lucide-react";
import "./App.css";

const API_URL = "https://pack-manager-api.onrender.com";

function App() {
  const [orgId, setOrgId] = useState("org_demo_alpha");
  const [orderId, setOrderId] = useState("ORD-TEST-UI-001");
  const [orderLines, setOrderLines] = useState(
    "TSHIRT-BLK:1;CAP-BLU:1;SOCK-RED:1"
  );
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleImageChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    setImage(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setError("");
  }

  async function verifyPackage() {
    if (!image) {
      setError("Upload a package photo first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();

    formData.append("org_id", orgId);
    formData.append("order_id", orderId);
    formData.append("order_lines", orderLines);
    formData.append("image", image);

    try {
      const response = await fetch(
        `${API_URL}/verify`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Verification request failed.");
      }

      const data = await response.json();

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const decision = result?.decision;

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <PackageCheck size={22} />
          </div>

          <div>
            <h1>Pack Manager</h1>
            <span>AI Packing Verification</span>
          </div>
        </div>

        <div className="status">
          <span className="status-dot" />
          System Online
        </div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">OUTBOUND VERIFICATION</p>

          <h2>
            Verify the box
            <br />
            <span>before it ships.</span>
          </h2>

          <p className="subtitle">
            Upload an open-package photo and let Pack Manager
            compare what was picked against the customer order.
          </p>
        </div>
      </section>

      <section className="workspace">
        <div className="panel">
          <div className="panel-title">
            <Camera size={20} />
            <div>
              <h3>Package capture</h3>
              <p>Upload a clear photo of the open box.</p>
            </div>
          </div>

          <label className="upload">
            {preview ? (
              <img src={preview} alt="Package preview" />
            ) : (
              <>
                <Upload size={34} />
                <strong>Upload package photo</strong>
                <span>JPG, PNG or WEBP</span>
              </>
            )}

            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
            />
          </label>
        </div>

        <div className="panel">
          <div className="panel-title">
            <PackageCheck size={20} />

            <div>
              <h3>Order details</h3>
              <p>What should be inside the box?</p>
            </div>
          </div>

          <label>
            Organization
            <input
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
            />
          </label>

          <label>
            Order ID
            <input
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
            />
          </label>

          <label>
            Order lines
            <input
              value={orderLines}
              onChange={(e) => setOrderLines(e.target.value)}
            />
          </label>

          <button
            className="verify-button"
            onClick={verifyPackage}
            disabled={loading}
          >
            {loading ? "Verifying..." : "Verify Package"}
          </button>
        </div>
      </section>

      {error && (
        <div className="error">
          <AlertTriangle size={20} />
          {error}
        </div>
      )}

      {result && (
        <section className="result">
          <div className={`decision ${decision}`}>
            {decision === "seal" && <CheckCircle2 size={34} />}
            {decision === "stop_and_fix" && (
              <AlertTriangle size={34} />
            )}
            {decision === "pending" && <Clock3 size={34} />}

            <div>
              <span>PACKING DECISION</span>

              <h2>
                {decision === "seal" && "SEAL"}
                {decision === "stop_and_fix" && "STOP & FIX"}
                {decision === "pending" && "PENDING REVIEW"}
              </h2>
            </div>
          </div>

          <div className="reason">
            {result.verification_status === "uncertain" && (
              <strong>⚠️ Verification uncertain — human review required.</strong>
            )}

            {result.verification_status !== "uncertain" && result.reason}
          </div>

          <div className="checks">
            {result.checks?.map((check) => (
              <div
                className="check"
                key={check.sku}
              >
                <div>
                  <strong>{check.sku}</strong>
                  <div className="check" key={check.sku}>
                  <div>
                    <strong>{check.sku}</strong>
                    <span>{check.reason}</span>

                    {result.observed_items
                      ?.filter((item) => item.sku === check.sku)
                      .map((item) => (
                        <small className="evidence" key={item.sku}>
                          Evidence: {item.evidence}
                        </small>
                      ))}
                  </div>

                  <div className="quantity">
                    <b>{check.observed_quantity}</b>
                    <span>/</span>
                    <b>{check.expected_quantity}</b>
                  </div>

                  <span className={`badge ${check.status}`}>
                    {check.status}
                  </span>
                </div>
                </div>

                <div className="quantity">
                  <b>{check.observed_quantity}</b>
                  <span>/</span>
                  <b>{check.expected_quantity}</b>
                </div>

                <span className={`badge ${check.status}`}>
                  {check.status}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
import React, { useState } from "react";
import "./App.css";

function App() {
  const [response1, setResponse1] = useState("");
  const [response2, setResponse2] = useState("");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [prolificId, setProlificId] = useState("");

  const [showFeedback, setShowFeedback] = useState(false);
  const [showTextbox2, setShowTextbox2] = useState(false);

  const API_BASE =
    window.location.hostname === "localhost"
      ? "http://127.0.0.1:8000"
      : "https://backend-clbs.onrender.com";

  // ✅ Scenario text (FULL paragraph)
  const scenarioText = `
A group of friends set up a hammock using springs attached to a metal frame.
After using the hammock for a few days, the friends noticed that the springs
stretched to a different distance when different people used the hammock.
They noticed that doubling the weight of a person would cause the springs
to stretch twice as far.

The friends initially thought it was a problem with the springs and ordered
a new set. The new set of springs stretched even more but showed the same
pattern: the stretch distance doubled if the weight doubled.
`;

  // ✅ Highlighted question
  const questionText =
    "Can you suggest a mathematical relationship between the variables in this problem that could explain why the new set of springs stretches more than the original springs? Justify your answer.";

  const extractFeedback = (data) => {
    let cleanFeedback = "No feedback received.";

    if (typeof data.feedback === "string") {
      cleanFeedback = data.feedback;
    } else if (data.feedback && typeof data.feedback === "object") {
      cleanFeedback =
        data.feedback.feedback ||
        data.feedback.Feedback ||
        data.feedback.message ||
        data.feedback.text ||
        JSON.stringify(data.feedback);
    } else if (data.Feedback_Text) {
      cleanFeedback = data.Feedback_Text;
    } else if (data.message) {
      cleanFeedback = data.message;
    } else if (data.result) {
      cleanFeedback = data.result;
    }

    return cleanFeedback
      .replace(/undefined/g, "")
      .replace(/^["'{\s]+|["'}\s]+$/g, "")
      .trim();
  };

  const typeFeedback = (text) => {
    setFeedback("");
    setShowFeedback(true);
    setShowTextbox2(false);

    const words = text.split(" ").filter(Boolean);
    let index = 0;

    const interval = setInterval(() => {
      if (index >= words.length) {
        clearInterval(interval);
        setShowTextbox2(true);
        return;
      }

      setFeedback((prev) =>
        prev ? prev + " " + words[index] : words[index]
      );

      index++;
    }, 40);
  };

  const handleSubmit = async () => {
    if (!prolificId.trim()) {
      alert("Please enter your Prolific ID.");
      return;
    }

    if (!response1.trim()) {
      alert("Please enter your answer in Textbox 1.");
      return;
    }

    setLoading(true);
    setFeedback("");
    setShowFeedback(false);
    setShowTextbox2(false);

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          prolific_id: prolificId,
          student_response_1: response1,
          student_response_2: ""
        })
      });

      if (!res.ok) throw new Error("Backend error");

      const data = await res.json();
      const cleanFeedback = extractFeedback(data);
      typeFeedback(cleanFeedback);
    } catch (error) {
      console.error(error);
      setShowFeedback(true);
      setFeedback("Something went wrong. Please check backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleResubmit = () => {
    if (!response2.trim()) {
      alert("Please enter your improved answer.");
      return;
    }

    alert("Thank you for submitting your answer, please close the window and return to the survey.");
  };

  return (
    <div className="page">
      <div className="card">

        {/* ✅ Scenario + Question Section */}
        <div className="prompt-section">

          <p className="scenario-text">
            {scenarioText}
          </p>

          <p className="highlighted-question">
            {questionText}
          </p>

        </div>

        {/* Image */}
        <img
          src="/question.png"
          alt="Hammock spring question"
          className="question-image"
        />

        {/* Prolific ID */}
        <div className="student-input">
          <label>Prolific ID</label>
          <input
            type="text"
            value={prolificId}
            onChange={(e) => setProlificId(e.target.value)}
            placeholder="Enter your Prolific ID..."
          />
        </div>

        {/* Textbox 1 */}
        <textarea
          className="answer-box"
          value={response1}
          onChange={(e) => setResponse1(e.target.value)}
          placeholder="Textbox 1: Enter your answer"
        />

        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? "Generating Feedback..." : "Submit"}
        </button>

        {/* Feedback */}
        {showFeedback && (
          <div className="feedback-box">
            <div className="feedback-label">Feedback</div>
            <p>{feedback}</p>
          </div>
        )}

        {/* Textbox 2 */}
        {showTextbox2 && (
          <>
            <textarea
              className="answer-box"
              value={response2}
              onChange={(e) => setResponse2(e.target.value)}
              placeholder="Textbox 2: Improve your answer"
            />

            <button className="submit-btn" onClick={handleResubmit}>
              Resubmit
            </button>
          </>
        )}

      </div>
    </div>
  );
}

export default App;
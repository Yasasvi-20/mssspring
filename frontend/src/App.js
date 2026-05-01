import React, { useState } from "react";
import "./App.css";

function App() {
  const [response1, setResponse1] = useState("");
  const [response2, setResponse2] = useState("");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [studentName, setStudentName] = useState("");

  const API_BASE =
    window.location.hostname === "localhost"
      ? "http://127.0.0.1:8000"
      : "https://backend-clbs.onrender.com";

  const typeFeedback = (text) => {
  setFeedback("");

  const words = text.split(" ");
  let index = 0;

  const interval = setInterval(() => {
    setFeedback((prev) =>
      prev ? prev + " " + words[index] : words[index]
    );

    index++;

    if (index >= words.length) {
      clearInterval(interval);
    }
  }, 45);
};

  const handleSubmit = async () => {
  if (!studentName.trim()) {
  setFeedback("Please enter your name before submitting.");
  return;
}

if (!response1.trim()) {
  setFeedback("Please enter your answer in Text Box 1 before submitting.");
  return;
}

    setLoading(true);
    setFeedback("");

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
            student_name: studentName,
          student_response_1: response1,
          student_response_2: response2,
        }),
      });

      if (!res.ok) {
        throw new Error("Backend error");
      }

      const data = await res.json();

      let cleanFeedback = "No feedback received.";

      if (data.feedback) {
        if (typeof data.feedback === "string") {
          let cleaned = data.feedback
            .replace(/```json/g, "")
            .replace(/```/g, "")
            .trim();

          try {
            const parsed = JSON.parse(cleaned);
            cleanFeedback =
              parsed.feedback_text || parsed.feedback || cleaned;
          } catch {
            cleanFeedback = cleaned;
          }
        } else {
          cleanFeedback =
            data.feedback.feedback_text ||
            data.feedback.feedback ||
            JSON.stringify(data.feedback);
        }
      } else if (data.feedback_text) {
        cleanFeedback = data.feedback_text;
      }

      typeFeedback(cleanFeedback);
    } catch (error) {
      console.error(error);
      setFeedback(
        "Something went wrong. Please check if the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="card">
        <h1 className="title">Hammock Springs and Hooke&apos;s Law</h1>


        <p className="question-text">
          Look at the picture below. Explain how the spring stretch changes
          when force is applied to the hammock.
        </p>
    <div className="student-input">
  <label>Student Name</label>
  <input
    type="text"
    value={studentName}
    onChange={(e) => setStudentName(e.target.value)}
    placeholder="Enter your name..."
  />
</div>
        <div className="content-row">
          <div className="image-section">
            <img
              src="/question.png"
              alt="Hammock spring question"
              className="question-image"
            />
          </div>

          <div className="answer-section">
            <label>Text Box 1</label>
            <textarea
              value={response1}
              onChange={(e) => setResponse1(e.target.value)}
              placeholder="Write your first answer here..."
            />

            <label>Text Box 2</label>
            <textarea
              value={response2}
              onChange={(e) => setResponse2(e.target.value)}
              placeholder="Write your improved answer here..."
            />

            <button onClick={handleSubmit} disabled={loading}>
              {loading ? "Generating Feedback..." : "Submit"}
            </button>
          </div>
        </div>

        <div className="feedback-box">
          <h2>Feedback</h2>
          <p>
            {feedback ||
              "Your feedback will appear here after submitting your answer."}
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
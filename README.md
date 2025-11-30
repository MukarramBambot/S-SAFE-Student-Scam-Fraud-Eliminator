# S-SAFE — Student Scam & Fraud Eliminator

An AI-powered multi-agent system designed to protect students from fake job postings, scam internships, and fraud recruitment.

## 🚀 Features
- **Multi-Agent Architecture**: Input, Pattern, ML, Salary, and Decision agents.
- **Scam Detection**: Identifies payment scams, unrealistic salaries, and suspicious patterns.
- **Gemini AI Integration**: Uses Google's Gemini Flash for reasoning and explanation.
- **Python 3.14 Compatible**: Lightweight stack without heavy dependencies.

## 🛠️ Installation

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set API Key**:
    ```bash
    export GEMINI_API_KEY="your_api_key_here"
    ```

## ▶️ Usage

Run the project with a single command:

```bash
python launch.py
```

This will start the backend server and automatically open the web interface in your browser.

## 📂 Structure
- `s_safe/`: Core agent logic and backend.
- `frontend/`: HTML/CSS/JS user interface.
- `model/`: (Optional) ML models (disabled in Python 3.14 mode).

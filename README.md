# Property Risk Analyzer

An AI-powered web application that helps underwriters quickly identify key risk factors from property inspection reports. The app uses OpenAI's GPT-3.5-turbo to analyze complex inspection documents and provides real-time thinking traces to show the AI's reasoning process.

## 🚀 Features

### **AI-Powered Analysis**
- **Real-time Risk Assessment**: Analyzes property inspection reports (PDF/text) for risk factors
- **Live Thinking Traces**: Watch the AI's reasoning process unfold in real-time
- **Section-by-Section Analysis**: Breaks down analysis into 8 key property areas
- **Comprehensive Risk Scoring**: Provides severity levels and recommendations

### **Interactive UI**
- **File Upload**: Support for PDF and text files
- **Live Streaming**: Real-time progress updates during analysis
- **Thinking Traces Panel**: Shows AI reasoning during and after analysis
- **Export Functionality**: Download analysis results as CSV
- **Responsive Design**: Works on desktop and mobile devices

### **Analysis Sections**
The AI analyzes these key property areas:
- **Structural Assessment**
- **Electrical Systems**
- **Plumbing Systems**
- **HVAC Systems**
- **Safety Concerns**
- **Environmental Issues**
- **Accessibility**
- **Property Condition**

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **AI**: OpenAI GPT-3.5-turbo API
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **PDF Processing**: PyPDF2
- **Data Export**: Pandas CSV export

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Git

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd property-risk-analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🚀 Usage

1. **Start the server**
   ```bash
   source venv/bin/activate
   python app.py
   ```

2. **Access the application**
   Open your browser and go to: `http://localhost:5001`

3. **Upload a property inspection report**
   - Click "Choose File" and select a PDF or text file
   - Watch the AI analyze the document in real-time
   - View thinking traces as the analysis progresses
   - Review the final risk assessment
   - Export results to CSV if needed

## 📊 Sample Data

The project includes a sample inspection report (`sample_inspection.txt`) for testing purposes.

## 🔍 How It Works

1. **File Upload**: User uploads a property inspection report
2. **Text Extraction**: App extracts text from PDF or reads text file
3. **Real-time Analysis**: AI analyzes each section with live streaming updates
4. **Thinking Traces**: Shows AI's reasoning process for each section
5. **Risk Assessment**: Generates comprehensive risk analysis
6. **Results Display**: Presents findings with severity levels and recommendations

## 🎯 Benefits for Underwriters

- **Time Savings**: Quickly identify key risk factors from long reports
- **Transparency**: See exactly how the AI reached its conclusions
- **Consistency**: Standardized analysis across different reports
- **Audit Trail**: Complete record of analysis process
- **Risk Prioritization**: Clear severity levels and recommendations

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Customization
You can modify the analysis sections in `app.py` by editing the `sections` list in the `stream_analysis` function.

## 📁 Project Structure

```
property-risk-analyzer/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore rules
├── README.md            # This file
├── static/
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── app.js       # Frontend JavaScript
├── templates/
│   └── index.html       # Main HTML template
├── sample_inspection.txt # Sample data for testing
└── venv/                # Virtual environment (not in repo)
```

## 🐛 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'pandas'"**
   - Make sure virtual environment is activated
   - Run: `pip install pandas`

2. **"OpenAI API key not found"**
   - Create `.env` file with your API key
   - Format: `OPENAI_API_KEY=your_key_here`

3. **Port 5000 in use**
   - App runs on port 5001 by default
   - If needed, change port in `app.py`

4. **JSON parsing errors**
   - Usually indicates API response issues
   - Check your OpenAI API key and quota

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for personal use. Please ensure you comply with OpenAI's terms of service when using their API.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-3.5-turbo API
- Flask team for the web framework
- Bootstrap for the UI components

---

**Note**: This application requires an OpenAI API key and will incur costs based on API usage. Please review OpenAI's pricing and terms of service. 
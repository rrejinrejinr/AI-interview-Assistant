import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Award, FileText, CheckCircle, AlertCircle, User, Mail, Phone, 
  Briefcase, ShieldAlert, ShieldCheck, Check, Info, Sparkles, 
  TrendingUp, Compass, Cpu, Target, ThumbsUp, ThumbsDown, Activity, ChevronRight,
  Upload, BarChart2, Code, HelpCircle, MessageSquare, Clock
} from 'lucide-react';


// Translations Dictionary for Multi-language Support (English, Hindi, Tamil)
const TRANSLATIONS = {
  en: {
    // Navigation
    uploadResume: "Upload Resume",
    atsResults: "ATS Results",
    skillsAnalysis: "Skills Analysis",
    interviewPrep: "Interview Prep",
    aiCoach: "AI Coach",
    history: "History",
    aboutSupport: "About & Support",
    resumeBuilder: "AI Resume Builder",
    backendOnline: "Backend: Online",
    backendOffline: "Backend: Offline (Demo)",
    
    // Upload page
    uploadTitle: "Upload Resume",
    uploadSubtitle: "Analyze your resume against job specifications to extract details, recommended roles, and scores.",
    dragDropText: "Drag & drop your resume PDF here",
    clickBrowseText: "or click to browse your folders (Max 10MB)",
    jobDescLabel: "Job Description (Optional)",
    jobDescPlaceholder: "Paste the job specifications here to run comparison and calculate tailored skill fit...",
    analyzingText: "Analyzing PDF using TF-IDF models and calculating job recommendations...",
    analyzeBtn: "🚀 Analyze Resume",
    
    // ATS results page
    atsTitle: "ATS Scorecard",
    atsScoreLabel: "ATS SCORE",
    skillsFound: "Skills Found",
    atsMatchIndex: "ATS Match Index",
    matched: "Matched",
    missing: "Missing",
    mlRecommendations: "Job Role Recommendations",
    candidateProfile: "Candidate Profile",
    emailContact: "Email Contact",
    phoneContact: "Phone Contact",
    estExperience: "Estimated Experience",
    matchedSkillsTitle: "Matched Skills",
    missingSkillsTitle: "Missing Skills",
    noneMatched: "None Matched",
    noneMissing: "None Missing",
    skillTip: "Skill Optimization Tip",
    warningScore: "ATS Score is below threshold (60%). Adding the missing core technologies identified below will improve your relevance index and keyword matches.",
    
    // Skills page
    skillsTitle: "Extracted Skills Breakdown",
    skillsSubtitle: "Skills detected from NLP parser grouped by category.",
    allSkillsDetected: "All Extracted Resume Skills",
    totalSkills: "Total",
    noSkillsDetected: "No skills detected in this category.",
    
    // Prep page
    prepTitle: "Interactive Mock Interview",
    prepSubtitle: "Practice answers for specific questions using typing or Speech-to-Text and receive real-time AI evaluations.",
    technicalQuestions: "Technical Questions",
    behavioralQuestions: "Behavioral Questions",
    activeQuestionLabel: "ACTIVE QUESTION",
    yourResponseLabel: "Your Response",
    responsePlaceholder: "Type your answer, or click the Record button below to speak...",
    recordBtn: "🎙️ Record Voice",
    stopBtn: "🛑 Stop Recording",
    evaluatingBtn: "Evaluating Answer...",
    evaluateBtn: "🚀 Evaluate Answer",
    feedbackTitle: "AI Answer Feedback",
    scoreText: "Score",
    correctPoints: "Correct Points Mentioned",
    missingConcepts: "Missing Technical Concepts",
    tipsImprovement: "Tips for Improvement",
    idealModelAnswer: "Ideal Model Answer",
    selectQuestionPrompt: "Select a question from the left panel to begin.",
    
    // Coach page
    coachTitle: "AI Interview Coach",
    coachSubtitle: "Chat with Claude to practice your answers and receive personalized feedback.",
    claudeKeyLabel: "Anthropic Claude Key:",
    claudePlaceholder: "Paste your Anthropic API Key (sk-ant-...) here to speak with Claude",
    savedLocal: "Saved Local",
    simulatorMode: "Simulator Mode",
    sendBtn: "Send",
    
    // History page
    historyTitle: "Analysis History",
    historySubtitle: "View and reload your 10 most recent resume matching records.",
    noAnalyses: "No analyses in H2 database. Try uploading a resume first in the upload page!",
    
    // About & Support page
    aboutSupportTitle: "About Project & Support",
    aboutSupportSubtitle: "Learn more about this platform's technologies and contact the developer.",
    aboutProjectHeading: "ℹ️ About the Project",
    projectVersion: "Version",
    techUsed: "Technologies Used",
    devInfoHeading: "💻 Developer Profile",
    devName: "Name",
    devRole: "Role",
    devEmail: "Email",
    devGithub: "GitHub",
    devLinkedin: "LinkedIn",
    contactSupportHeading: "📬 Help & Support Contact",
    supportDesc: "Send a message to our support desk. The contact details are pre-filled below.",
    formNameLabel: "Your Name",
    formEmailLabel: "Your Email Address",
    formMessageLabel: "Message",
    formMessagePlaceholder: "Type your query, suggestion, or message here...",
    submitFormBtn: "Submit Support Ticket",
    ticketSubmittedTitle: "Ticket Submitted!",
    ticketSubmittedMsg: "Thank you for contacting us! We will review your message and reach out shortly.",
    backToAppBtn: "Back to App"
  },
  hi: {
    // Navigation
    uploadResume: "रिज्यूमे अपलोड करें",
    atsResults: "एटीएस परिणाम",
    skillsAnalysis: "कौशल विश्लेषण",
    interviewPrep: "इंटरव्यू की तैयारी",
    aiCoach: "एआई कोच",
    history: "इतिहास",
    aboutSupport: "परिचय और सहायता",
    resumeBuilder: "एआई रेज़्यूमे बिल्डर",
    backendOnline: "बैकएंड: ऑनलाइन",
    backendOffline: "बैकएंड: ऑफ़लाइन (डेमो)",
    
    // Upload page
    uploadTitle: "रिज्यूमे अपलोड करें",
    uploadSubtitle: "विवरण, अनुशंसित भूमिकाएं और स्कोर प्राप्त करने के लिए जॉब डिस्क्रिप्शन के साथ अपने रिज्यूमे का विश्लेषण करें।",
    dragDropText: "अपना रिज्यूमे पीडीएफ यहां ड्रैग और ड्रॉप करें",
    clickBrowseText: "या अपनी फाइलों से चुनने के लिए क्लिक करें (अधिकतम 10MB)",
    jobDescLabel: "जॉब डिस्क्रिप्शन (वैकल्पिक)",
    jobDescPlaceholder: "तुलना करने और कौशल मिलान स्कोर की गणना करने के लिए जॉब डिस्क्रिप्शन यहां पेस्ट करें...",
    analyzingText: "टीएफ-आईडीएफ मॉडल का उपयोग करके रिज्यूमे का विश्लेषण किया जा रहा है...",
    analyzeBtn: "🚀 रिज्यूमे का विश्लेषण करें",
    
    // ATS results page
    atsTitle: "एटीएस स्कोरकार्ड",
    atsScoreLabel: "एटीएस स्कोर",
    skillsFound: "पाए गए कौशल",
    atsMatchIndex: "मैच इंडेक्स",
    matched: "मैच हुए",
    missing: "लापता कौशल",
    mlRecommendations: "नौकरी की भूमिका के लिए सिफारिशें",
    candidateProfile: "उम्मीदवार प्रोफाइल",
    emailContact: "ईमेल संपर्क",
    phoneContact: "फोन संपर्क",
    estExperience: "अनुमानित अनुभव",
    matchedSkillsTitle: "मैच हुए कौशल",
    missingSkillsTitle: "लापता कौशल",
    noneMatched: "कोई मैच नहीं मिला",
    noneMissing: "कोई कौशल लापता नहीं",
    skillTip: "कौशल अनुकूलन टिप",
    warningScore: "एटीएस स्कोर 60% से कम है। नीचे दिए गए कौशल जोड़ने से आपका मैच इंडेक्स बेहतर होगा।",
    
    // Skills page
    skillsTitle: "कौशल विश्लेषण",
    skillsSubtitle: "पायथन एनएलपी पार्सर द्वारा श्रेणियों में बांटे गए आपके कौशल।",
    allSkillsDetected: "रिज्यूमे से पाए गए सभी कौशल",
    totalSkills: "कुल",
    noSkillsDetected: "इस श्रेणी में कोई कौशल नहीं पाया गया।",
    
    // Prep page
    prepTitle: "इंटरएक्टिव मॉक इंटरव्यू",
    prepSubtitle: "लिखकर या बोलकर उत्तरों का अभ्यास करें और तुरंत एआई प्रतिक्रिया प्राप्त करें।",
    technicalQuestions: "तकनीकी प्रश्न",
    behavioralQuestions: "व्यवहार संबंधी प्रश्न",
    activeQuestionLabel: "सक्रिय प्रश्न",
    yourResponseLabel: "आपका उत्तर",
    responsePlaceholder: "अपना उत्तर लिखें, या बोलने के लिए नीचे दिए गए बटन पर क्लिक करें...",
    recordBtn: "🎙️ आवाज रिकॉर्ड करें",
    stopBtn: "🛑 रिकॉर्डिंग रोकें",
    evaluatingBtn: "उत्तर का मूल्यांकन किया जा रहा है...",
    evaluateBtn: "🚀 उत्तर का मूल्यांकन करें",
    feedbackTitle: "एआई उत्तर प्रतिक्रिया",
    scoreText: "स्कोर",
    correctPoints: "आपके उत्तर में सही बिंदु",
    missingConcepts: "उत्तर में लापता अवधारणाएं",
    tipsImprovement: "सुधार के सुझाव",
    idealModelAnswer: "आदर्श मॉडल उत्तर",
    selectQuestionPrompt: "शुरू करने के लिए बाएं पैनल से एक प्रश्न चुनें।",
    
    // Coach page
    coachTitle: "एआई इंटरव्यू कोच",
    coachSubtitle: "क्लोड एआई के साथ अभ्यास करें और व्यक्तिगत प्रतिक्रिया प्राप्त करें।",
    claudeKeyLabel: "क्लोड एपीआई कुंजी:",
    claudePlaceholder: "बातचीत करने के लिए अपनी एपीआई कुंजी यहां पेस्ट करें",
    savedLocal: "सहेजा गया",
    simulatorMode: "सिम्युलेटर मोड",
    sendBtn: "भेजें",
    
    // History page
    historyTitle: "इतिहास",
    historySubtitle: "अपने पिछले 10 रिज्यूमे विश्लेषण परिणाम देखें।",
    noAnalyses: "डेटाबेस में कोई रिकॉर्ड नहीं है। कृपया पहले एक रिज्यूमे अपलोड करें।",
    
    // About & Support page
    aboutSupportTitle: "परियोजना और सहायता",
    aboutSupportSubtitle: "उपयोग की गई तकनीकों और डेवलपर के बारे में जानकारी।",
    aboutProjectHeading: "ℹ️ परियोजना के बारे में",
    projectVersion: "संस्करण",
    techUsed: "उपयोग की गई तकनीकें",
    devInfoHeading: "💻 डेवलपर प्रोफाइल",
    devName: "नाम",
    devRole: "भूमिका",
    devEmail: "ईमेल",
    devGithub: "गिटहब",
    devLinkedin: "लिंक्डइन",
    contactSupportHeading: "📬 सहायता फॉर्म",
    supportDesc: "सहायता के लिए संदेश भेजें। संपर्क विवरण नीचे दिए गए हैं।",
    formNameLabel: "आपका नाम",
    formEmailLabel: "आपका ईमेल",
    formMessageLabel: "संदेश",
    formMessagePlaceholder: "अपना संदेश यहां लिखें...",
    submitFormBtn: "संदेश भेजें",
    ticketSubmittedTitle: "संदेश भेजा गया!",
    ticketSubmittedMsg: "हमसे संपर्क करने के लिए धन्यवाद! हम जल्द ही आपसे संपर्क करेंगे।",
    backToAppBtn: "वापस जाएं"
  },
  ta: {
    // Navigation
    uploadResume: "விவரக்குறிப்பை பதிவேற்றுக",
    atsResults: "ஏடிஎஸ் முடிவுகள்",
    skillsAnalysis: "திறன் பகுப்பாய்வு",
    interviewPrep: "நேர்காணல் தயாரிப்பு",
    aiCoach: "ஏஐ பயிற்சி",
    history: "வரலாறு",
    aboutSupport: "தகவல்கள் & உதவி",
    resumeBuilder: "ஏஐ ரெஸ்யூம் பில்டர்",
    backendOnline: "சர்வர்: ஆன்லைன்",
    backendOffline: "சர்வர்: ஆஃப்லைன் (டெமோ)",
    
    // Upload page
    uploadTitle: "விவரக்குறிப்பை பதிவேற்றுக",
    uploadSubtitle: "உங்கள் திறன்கள், பரிந்துரைக்கப்பட்ட பணிகள் மற்றும் மதிப்பெண்களை கணக்கிட உங்கள் விவரக்குறிப்பை ஒப்பிடுக.",
    dragDropText: "உங்கள் பி.டி.எஃப் விவரக்குறிப்பை இங்கே இழுத்து விடவும்",
    clickBrowseText: "அல்லது உங்கள் கோப்புகளைத் தேர்ந்தெடுக்க இங்கே கிளிக் செய்யவும் (அதிகபட்சம் 10MB)",
    jobDescLabel: "வேலை விவரம் (விருப்பத்தேர்வு)",
    jobDescPlaceholder: "வேலை தகுதிகளை இங்கே ஒட்டவும்...",
    analyzingText: "விவரக்குறிப்பு பகுப்பாய்வு செய்யப்படுகிறது, தயவுசெய்து காத்திருக்கவும்...",
    analyzeBtn: "🚀 விவரக்குறிப்பை பகுப்பாய்வு செய்க",
    
    // ATS results page
    atsTitle: "ஏடிஎஸ் மதிப்பெண் அட்டை",
    atsScoreLabel: "ஏடிஎஸ் மதிப்பெண்",
    skillsFound: "கண்டறியப்பட்ட திறன்கள்",
    atsMatchIndex: "பொருத்தம் குறியீடு",
    matched: "பொருந்தியவை",
    missing: "இல்லாதவை",
    mlRecommendations: "வேலை வாய்ப்பு பரிந்துரைகள்",
    candidateProfile: "விண்ணப்பதாரர் சுயவிவரம்",
    emailContact: "மின்னஞ்சல் முகவரி",
    phoneContact: "தொலைபேசி எண்",
    estExperience: "பணி அனுபவம்",
    matchedSkillsTitle: "பொருந்திய திறன்கள்",
    missingSkillsTitle: "இல்லாத திறன்கள்",
    noneMatched: "பொருந்தக்கூடிய திறன்கள் எதுவும் இல்லை",
    noneMissing: "குறைபாடுகள் எதுவும் இல்லை",
    skillTip: "மதிப்பெண் அதிகரிக்க வழி",
    warningScore: "உங்கள் ஏடிஎஸ் மதிப்பெண் 60% ஐ விடக் குறைவாக உள்ளது. கீழே உள்ள திறன்களைச் சேர்ப்பது மதிப்பெண்ணை அதிகரிக்க உதவும்.",
    
    // Skills page
    skillsTitle: "திறன்கள் பகுப்பாய்வு",
    skillsSubtitle: "உங்கள் விவரக்குறிப்பில் இருந்து கண்டறியப்பட்ட திறன்கள் வகைப்படுத்தப்பட்டுள்ளன.",
    allSkillsDetected: "கண்டறியப்பட்ட அனைத்து திறன்களும்",
    totalSkills: "மொத்தம்",
    noSkillsDetected: "இந்த பிரிவில் திறன்கள் எதுவும் கண்டறியப்படவில்லை.",
    
    // Prep page
    prepTitle: "ஊடாடும் போலி நேர்காணல்",
    prepSubtitle: "எழுதியோ அல்லது பேசியோ பதிலளித்து ஏஐ மதிப்பீட்டை உடனுக்குடன் பெறுங்கள்.",
    technicalQuestions: "தொழில்நுட்ப கேள்விகள்",
    behavioralQuestions: "நடத்தை கேள்விகள்",
    activeQuestionLabel: "செயலில் உள்ள கேள்வி",
    yourResponseLabel: "உங்கள் பதில்",
    responsePlaceholder: "உங்கள் பதிலை எழுதவும், அல்லது பேச குரல் பதிவு பொத்தானை அழுத்தவும்...",
    recordBtn: "🎙️ பேசுக",
    stopBtn: "🛑 பதிவை நிறுத்துக",
    evaluatingBtn: "பதில் மதிப்பிடப்படுகிறது...",
    evaluateBtn: "🚀 பதிலைச் சமர்ப்பிக்கவும்",
    feedbackTitle: "ஏஐ பதில் மதிப்பீடு",
    scoreText: "மதிப்பெண்",
    correctPoints: "நீங்கள குறிப்பிட்ட சரியான புள்ளிகள்",
    missingConcepts: "பதிலில் விடுபட்ட தொழில்நுட்ப கருத்துக்கள்",
    tipsImprovement: "மேம்படுத்துவதற்கான ஆலோசனைகள்",
    idealModelAnswer: "சிறந்த மாதிரி பதில்",
    selectQuestionPrompt: "தொடங்குவதற்கு இடது பலகத்தில் இருந்து ஒரு கேள்வியைத் தேர்ந்தெடுக்கவும்.",
    
    // Coach page
    coachTitle: "ஏஐ நேர்காணல் பயிற்சியாளர்",
    coachSubtitle: "உத்தரங்களைப் பயிற்சி செய்ய கிளோட் ஏஐ-யுடன் உரையாடவும்.",
    claudeKeyLabel: "கிளோட் API விசை:",
    claudePlaceholder: "கிளோடில் பேச உங்கள் API விசையை இங்கே ஒட்டவும்",
    savedLocal: "சேமிக்கப்பட்டது",
    simulatorMode: "சிமுலேட்டர் பயன்முறை",
    sendBtn: "அனுப்புக",
    
    // History page
    historyTitle: "பகுப்பாய்வு வரலாறு",
    historySubtitle: "உங்கள் முந்தைய 10 விவரக்குறிப்பு பகுப்பாய்வுகளைக் காண்க.",
    noAnalyses: "தரவுத்தளத்தில் பதிவுகள் எதுவும் இல்லை. முதலில் விவரக்குறிப்பை அப்லோட் செய்யவும்.",
    
    // About & Support page
    aboutSupportTitle: "திட்டம் & உதவி",
    aboutSupportSubtitle: "இந்த தளம் மற்றும் அதன் தொழில்நுட்பங்கள் பற்றி அறியவும்.",
    aboutProjectHeading: "ℹ️ திட்டம் பற்றி",
    projectVersion: "பதிப்பு",
    techUsed: "பயன்படுத்தப்பட்ட தொழில்நுட்பங்கள்",
    devInfoHeading: "💻 டெவலப்பர் சுயவிவரம்",
    devName: "பெயர்",
    devRole: "பதவி",
    devEmail: "மின்னஞ்சல்",
    devGithub: "கிட்ஹப்",
    devLinkedin: "லிங்க்ட்இன்",
    contactSupportHeading: "📬 உதவி கோரிக்கை படிவம்",
    supportDesc: "உதவிக்கு செய்தி அனுப்பவும். தொடர்பு விவரங்கள் கீழே தரப்பட்டுள்ளன.",
    formNameLabel: "உங்கள் பெயர்",
    formEmailLabel: "உங்கள் மின்னஞ்சல் முகவரி",
    formMessageLabel: "செய்தி",
    formMessagePlaceholder: "உங்கள் செய்தி அல்லது சந்தேகங்களை இங்கே எழுதவும்...",
    submitFormBtn: "செய்தியை அனுப்பவும்",
    ticketSubmittedTitle: "செய்தி அனுப்பப்பட்டது!",
    ticketSubmittedMsg: "எங்களைத் தொடர்பு கொண்டதற்கு நன்றி! உங்கள் செய்தியைப் பரிசீலித்து விரைவில் பதிலளிப்போம்.",
    backToAppBtn: "திரும்பச் செல்க"
  }
};

// Injected CSS Stylesheet
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

  :root {
    --bg-color: #0B1020;
    --card-bg: rgba(19, 27, 46, 0.65);
    --card-solid: #131B2E;
    --primary: #4F8CFF;
    --primary-glow: rgba(79, 140, 255, 0.15);
    --success: #22C55E;
    --success-glow: rgba(34, 197, 94, 0.15);
    --warning: #F59E0B;
    --warning-glow: rgba(245, 158, 11, 0.15);
    --danger: #EF4444;
    --danger-glow: rgba(239, 68, 68, 0.15);
    --text-primary: #FFFFFF;
    --text-secondary: #B8C1D9;
    --text-muted: #64748B;
    --border-color: rgba(255, 255, 255, 0.08);
    --sidebar-width: 240px;
    --sidebar-collapsed-width: 80px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  body {
    background-color: var(--bg-color);
    color: var(--text-secondary);
    font-family: 'Inter', sans-serif;
    overflow-x: hidden;
  }

  /* Custom Scrollbar */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    background: rgba(11, 16, 32, 0.5);
  }
  ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  /* Layout */
  .app-container {
    display: flex;
    min-height: 100vh;
    background-color: var(--bg-color);
  }

  /* Sidebar */
  .sidebar {
    width: var(--sidebar-width);
    background-color: rgba(12, 16, 32, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid var(--border-color);
    position: fixed;
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 24px 16px;
    z-index: 100;
    transition: var(--transition);
  }
  .sidebar.collapsed {
    width: var(--sidebar-collapsed-width);
    padding: 24px 12px;
  }

  .logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding: 0 8px;
  }
  .logo-icon {
    font-size: 24px;
    color: var(--primary);
    filter: drop-shadow(0 0 8px var(--primary-glow));
  }
  .logo-text {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 18px;
    letter-spacing: 0.5px;
    color: var(--text-primary);
  }

  .sidebar-toggle-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: var(--transition);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .sidebar-toggle-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }

  .lang-switcher-container {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    padding: 8px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
  .lang-label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    font-weight: 600;
  }
  .lang-buttons {
    display: flex;
    gap: 4px;
  }
  .lang-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 10px;
    font-weight: 700;
    padding: 4px 6px;
    border-radius: 4px;
    cursor: pointer;
    transition: var(--transition);
  }
  .lang-btn.active {
    background: var(--primary);
    color: var(--text-primary);
    box-shadow: 0 0 10px var(--primary-glow);
  }

  .user-sidebar-profile {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 8px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 24px;
  }
  .user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid var(--primary);
  }
  .user-info {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .user-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .user-email {
    font-size: 11px;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 4px;
  }
  .signout-btn {
    background: none;
    border: none;
    color: var(--danger);
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    text-align: left;
    padding: 0;
    transition: var(--transition);
  }
  .signout-btn:hover {
    text-decoration: underline;
  }

  .nav-menu {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex-grow: 1;
  }
  .nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: var(--transition);
    color: var(--text-secondary);
  }
  .nav-item:hover {
    background-color: rgba(255, 255, 255, 0.04);
    color: var(--text-primary);
  }
  .nav-item.active {
    background-color: var(--primary-glow);
    color: var(--primary);
    border-left: 3px solid var(--primary);
  }
  .nav-icon {
    font-size: 18px;
  }

  .sidebar-footer {
    margin-top: auto;
    padding: 8px;
  }
  .status-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
  }
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--danger);
    box-shadow: 0 0 8px var(--danger-glow);
  }
  .status-indicator.online {
    background-color: var(--success);
    box-shadow: 0 0 8px var(--success-glow);
  }

  /* Main Content Area */
  .main-content {
    flex-grow: 1;
    margin-left: var(--sidebar-width);
    padding: 40px;
    min-height: 100vh;
    transition: margin-left 0.3s ease;
  }
  .main-content.expanded {
    margin-left: var(--sidebar-collapsed-width);
  }

  /* Typography */
  .page-header {
    margin-bottom: 32px;
  }
  .page-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 8px;
    background: linear-gradient(135deg, #FFF 0%, #B8C1D9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .page-subtitle {
    font-size: 15px;
    color: var(--text-secondary);
    line-height: 1.6;
    max-width: 800px;
  }

  /* Glass Cards */
  .card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: var(--transition);
  }
  .card:hover {
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.45);
  }

  /* Premium Glass Cards */
  .premium-glass-card {
    background: rgba(20, 25, 45, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  }
  .premium-glass-card:hover {
    transform: translateY(-4px) !important;
    border-color: rgba(79, 140, 255, 0.25) !important;
    box-shadow: 0 12px 40px rgba(79, 140, 255, 0.15) !important;
  }

  /* Priority Chips */
  .priority-chip {
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: inline-flex;
    align-items: center;
  }
  .priority-chip-high {
    background: rgba(239, 68, 68, 0.15);
    color: #EF4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  .priority-chip-medium {
    background: rgba(245, 158, 11, 0.15);
    color: #F59E0B;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }
  .priority-chip-low {
    background: rgba(79, 140, 255, 0.15);
    color: #4F8CFF;
    border: 1px solid rgba(79, 140, 255, 0.3);
  }

  /* Vertical Timeline */
  .vertical-timeline {
    position: relative;
    padding-left: 28px;
    margin-left: 8px;
    border-left: 2px solid rgba(255, 255, 255, 0.05);
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .vertical-timeline-item {
    position: relative;
  }
  .vertical-timeline-dot {
    position: absolute;
    left: -37px;
    top: 4px;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #0B1020;
    border: 3px solid var(--primary);
    box-shadow: 0 0 10px var(--primary-glow);
    transition: all 0.3s ease;
  }
  .vertical-timeline-item:hover .vertical-timeline-dot {
    background: var(--primary);
    transform: scale(1.2);
  }
  .vertical-timeline-title {
    font-size: 13.5px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 4px;
  }
  .vertical-timeline-content {
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.5;
  }


  /* Stat Cards */
  .glass-stat-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transition: var(--transition);
  }
  .glass-stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--theme-color, var(--primary)), transparent);
  }
  .glow-blue { --theme-color: #4F8CFF; }
  .glow-purple { --theme-color: #a78bfa; }
  .glow-green { --theme-color: #22C55E; }
  .glow-red { --theme-color: #EF4444; }
  .glow-yellow { --theme-color: #F59E0B; }
  .glow-cyan { --theme-color: #06B6D4; }

  /* Login Screen */
  .login-screen {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: radial-gradient(circle at center, #131B2E 0%, #0B1020 100%);
    padding: 20px;
  }
  .login-card {
    width: 100%;
    max-width: 420px;
    background: rgba(19, 27, 46, 0.75);
    border: 1px solid var(--border-color);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    text-align: center;
  }
  .login-logo {
    font-size: 48px;
    color: var(--primary);
    margin-bottom: 24px;
    display: inline-block;
    filter: drop-shadow(0 0 16px var(--primary-glow));
  }
  .login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  .login-desc {
    color: var(--text-secondary);
    font-size: 14px;
    margin-bottom: 32px;
    line-height: 1.5;
  }
  .google-signin-btn-container {
    display: flex;
    justify-content: center;
    margin-bottom: 24px;
  }
  .divider {
    display: flex;
    align-items: center;
    color: var(--text-muted);
    font-size: 12px;
    margin: 24px 0;
  }
  .divider::before, .divider::after {
    content: '';
    flex-grow: 1;
    height: 1px;
    background: var(--border-color);
    margin: 0 12px;
  }

  /* Form Elements */
  .form-group {
    margin-bottom: 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    text-align: left;
  }
  .form-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .input-field, .form-textarea {
    background-color: rgba(11, 16, 32, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    padding: 12px 16px;
    font-size: 14px;
    transition: var(--transition);
    font-family: inherit;
  }
  .input-field:focus, .form-textarea:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 10px var(--primary-glow);
  }
  .form-textarea {
    resize: vertical;
    min-height: 100px;
  }

  /* Buttons */
  .btn {
    background: linear-gradient(135deg, var(--primary) 0%, #3B82F6 100%);
    color: var(--text-primary);
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  .btn:hover {
    opacity: 0.9;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px var(--primary-glow);
  }
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  .btn-outline {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-primary);
  }
  .btn-outline:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: var(--primary);
  }

  /* Upload Page specific */
  .upload-zone {
    border: 2px dashed var(--border-color);
    border-radius: 12px;
    padding: 48px 24px;
    text-align: center;
    cursor: pointer;
    transition: var(--transition);
    background: rgba(11, 16, 32, 0.2);
    margin-bottom: 24px;
  }
  .upload-zone:hover, .upload-zone.dragover {
    border-color: var(--primary);
    background: rgba(79, 140, 255, 0.02);
  }
  .upload-icon {
    font-size: 40px;
    color: var(--primary);
    margin-bottom: 16px;
    display: inline-block;
  }
  .upload-text {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 16px;
    margin-bottom: 6px;
  }
  .upload-subtext {
    font-size: 12px;
    color: var(--text-muted);
  }
  .selected-file-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(79, 140, 255, 0.1);
    border: 1px solid rgba(79, 140, 255, 0.2);
    padding: 6px 12px;
    border-radius: 20px;
    margin-top: 16px;
    font-size: 12px;
    color: var(--primary);
  }
  
  .instruction-step {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
  }
  .step-num {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--primary-glow);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
  }
  .step-text {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .supported-formats-badge {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .upload-progress-container {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    margin-top: 20px;
  }
  .progress-bar-bg {
    height: 6px;
    background: rgba(255,255,255,0.05);
    border-radius: 3px;
    overflow: hidden;
    position: relative;
    margin-top: 8px;
  }
  .progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary), #3b82f6);
    border-radius: 3px;
    width: 0%;
  }

  /* Radial Circle */
  .radial-score-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
  }
  .radial-score-svg {
    filter: drop-shadow(0 0 12px var(--ring-glow, rgba(79, 140, 255, 0.2)));
    transition: filter 0.3s ease;
  }
  .radial-circle-bg {
    fill: none;
    stroke: rgba(255, 255, 255, 0.03);
    stroke-width: 8px;
  }
  .radial-circle-val {
    fill: none;
    stroke-width: 8px;
    stroke-linecap: round;
    transform: rotate(-90deg);
    transform-origin: 50% 50%;
  }
  .radial-score-text {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .radial-score-num {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    color: var(--text-primary);
  }
  .radial-score-label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 2px;
  }

  .badge-neon {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .badge-neon-green {
    background: var(--success-glow);
    color: var(--success);
    border: 1px solid rgba(34, 197, 94, 0.3);
  }
  .badge-neon-cyan {
    background: rgba(6, 182, 212, 0.1);
    color: #06B6D4;
    border: 1px solid rgba(6, 182, 212, 0.3);
  }
  .badge-neon-yellow {
    background: var(--warning-glow);
    color: var(--warning);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }
  .badge-neon-red {
    background: var(--danger-glow);
    color: var(--danger);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  .badge-neon-purple {
    background: rgba(167, 139, 250, 0.1);
    color: #a78bfa;
    border: 1px solid rgba(167, 139, 250, 0.3);
  }

  /* Skill Pills */
  .pill-badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    transition: var(--transition);
    border: 1px solid transparent;
  }
  .pill-badge:hover {
    transform: scale(1.05);
  }
  .pill-green {
    background: var(--success-glow);
    color: var(--success);
    border-color: rgba(34, 197, 94, 0.2);
    box-shadow: 0 2px 8px var(--success-glow);
  }
  .pill-red {
    background: var(--danger-glow);
    color: var(--danger);
    border-color: rgba(239, 68, 68, 0.2);
    box-shadow: 0 2px 8px var(--danger-glow);
  }
  .pill-blue {
    background: var(--primary-glow);
    color: var(--primary);
    border-color: rgba(79, 140, 255, 0.2);
    box-shadow: 0 2px 8px var(--primary-glow);
  }
  .pill-yellow {
    background: var(--warning-glow);
    color: var(--warning);
    border-color: rgba(245, 158, 11, 0.2);
  }

  /* Redesigned Skill Pills with Rounded shape, glow, and animations */
  .skill-pill-badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 11.5px;
    font-weight: 600;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
    cursor: default;
  }
  .skill-pill-badge:hover {
    transform: translateY(-2px) scale(1.04);
  }
  .skill-pill-matched {
    background: rgba(34, 197, 94, 0.08);
    color: #22C55E;
    border-color: rgba(34, 197, 94, 0.2);
    box-shadow: 0 4px 10px rgba(34, 197, 94, 0.1);
  }
  .skill-pill-matched:hover {
    box-shadow: 0 6px 14px rgba(34, 197, 94, 0.25);
    background: rgba(34, 197, 94, 0.12);
  }
  .skill-pill-missing {
    background: rgba(239, 68, 68, 0.08);
    color: #EF4444;
    border-color: rgba(239, 68, 68, 0.2);
    box-shadow: 0 4px 10px rgba(239, 68, 68, 0.1);
  }
  .skill-pill-missing:hover {
    box-shadow: 0 6px 14px rgba(239, 68, 68, 0.25);
    background: rgba(239, 68, 68, 0.12);
  }
  .skill-pill-recommended {
    background: rgba(79, 140, 255, 0.08);
    color: #4F8CFF;
    border-color: rgba(79, 140, 255, 0.2);
    box-shadow: 0 4px 10px rgba(79, 140, 255, 0.1);
  }
  .skill-pill-recommended:hover {
    box-shadow: 0 6px 14px rgba(79, 140, 255, 0.25);
    background: rgba(79, 140, 255, 0.12);
  }


  /* Simulator */
  .simulator-skill-pill {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    cursor: pointer;
    transition: var(--transition);
  }
  .simulator-skill-pill:hover {
    background: rgba(255,255,255,0.08);
    border-color: var(--warning);
    color: var(--text-primary);
  }
  .simulator-skill-pill.simulated-added {
    background: var(--success-glow);
    border-color: var(--success);
    color: var(--success);
    box-shadow: 0 0 10px var(--success-glow);
  }

  /* Candidate Avatar Generator */
  .profile-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary) 0%, #a78bfa 100%);
    color: var(--text-primary);
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--border-color);
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
  }

  /* Sections analysis */
  .section-score-row {
    margin-bottom: 12px;
  }
  .section-score-label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--text-secondary);
  }
  .section-score-bar-bg {
    height: 6px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
    overflow: hidden;
  }
  .section-score-bar-fill {
    height: 100%;
    background: var(--primary);
    border-radius: 3px;
  }
  .section-score-bar-fill.weakest {
    background: var(--danger);
  }

  /* Optimizer Bullet Points comparison */
  .optimizer-bullet-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    background: rgba(11, 16, 32, 0.3);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
  }
  .bullet-label-weak {
    font-size: 9px;
    font-weight: 700;
    color: var(--danger);
    text-transform: uppercase;
    display: block;
    margin-bottom: 4px;
  }
  .bullet-label-optimized {
    font-size: 9px;
    font-weight: 700;
    color: var(--success);
    text-transform: uppercase;
    display: block;
    margin-bottom: 4px;
  }
  .bullet-text {
    font-size: 12px;
    line-height: 1.4;
  }

  /* Timeline */
  .roadmap-timeline {
    position: relative;
    padding-left: 20px;
    border-left: 2px solid var(--border-color);
    display: flex;
    flex-direction: column;
    gap: 24px;
    margin-top: 10px;
  }
  .roadmap-node {
    position: relative;
  }
  .roadmap-node-dot {
    position: absolute;
    left: -27px;
    top: 4px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--primary);
    border: 3px solid var(--bg-color);
    box-shadow: 0 0 8px var(--primary-glow);
  }
  .roadmap-node-title {
    font-weight: 700;
    font-size: 13px;
    color: var(--text-primary);
    margin-bottom: 6px;
  }

  /* Skills breakdown page */
  .category-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
  }
  .category-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding-bottom: 10px;
  }
  .category-title span:first-child {
    font-weight: 700;
    font-size: 14px;
    color: var(--text-primary);
  }
  .category-count {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 600;
  }
  .chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .chip {
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
  }
  .chip-violet {
    background: rgba(167, 139, 250, 0.05);
    border-color: rgba(167, 139, 250, 0.15);
    color: #a78bfa;
  }

  /* Grid layouts */
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  /* Empty state */
  .empty-state-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    max-width: 600px;
    margin: 40px auto;
  }

  /* Tab switchers */
  .tab-switcher {
    display: flex;
    background: rgba(255,255,255,0.02);
    padding: 4px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    margin-bottom: 24px;
    max-width: fit-content;
  }
  .tab-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 600;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    transition: var(--transition);
  }
  .tab-btn.active {
    background: var(--primary);
    color: var(--text-primary);
  }

  /* Prep page specific */
  .prep-layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 24px;
    align-items: start;
  }
  .question-list-pane {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: calc(100vh - 220px);
    overflow-y: auto;
    padding-right: 8px;
  }
  .question-item {
    display: flex;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-color);
    cursor: pointer;
    transition: var(--transition);
  }
  .question-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255,255,255,0.15);
  }
  .question-item.active {
    background: var(--primary-glow);
    border-color: var(--primary);
  }
  .question-num {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-primary);
  }
  .question-text {
    font-size: 12px;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  /* Speech wave */
  .speech-actions {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 12px;
  }
  .record-btn {
    background: var(--primary-glow);
    color: var(--primary);
    border: 1px solid rgba(79, 140, 255, 0.2);
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition);
  }
  .record-btn.recording {
    background: var(--danger-glow);
    color: var(--danger);
    border-color: rgba(239,68,68,0.2);
    animation: pulseRed 2s infinite;
  }
  @keyframes pulseRed {
    0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
    70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  }
  .speech-wave {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 16px;
  }
  .speech-bar {
    width: 3px;
    background: var(--danger);
    border-radius: 1px;
    animation: soundWave 1.2s ease-in-out infinite;
  }
  .speech-bar:nth-child(2) { animation-delay: 0.2s; height: 14px; }
  .speech-bar:nth-child(3) { animation-delay: 0.4s; height: 10px; }
  @keyframes soundWave {
    0%, 100% { height: 4px; }
    50% { height: 16px; }
  }

  /* Evaluation cards */
  .evaluation-card {
    background: rgba(11, 16, 32, 0.4);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 20px;
    margin-top: 20px;
  }
  .eval-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding-bottom: 12px;
    margin-bottom: 16px;
  }
  .eval-score-container {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .eval-score-ring {
    font-weight: 700;
    font-size: 14px;
    color: var(--success);
    background: var(--success-glow);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid rgba(34,197,94,0.2);
  }
  .eval-section-title {
    font-weight: 700;
    font-size: 12px;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 16px 0 6px 0;
  }
  .eval-section-content {
    font-size: 13px;
    line-height: 1.5;
  }
  .tips-list {
    padding-left: 20px;
    font-size: 13px;
    line-height: 1.5;
  }

  /* AI Coach chatbot UI */
  .chat-layout {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 200px);
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
  }
  .api-key-config {
    padding: 12px 20px;
    background: rgba(11,16,32,0.4);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .api-key-input {
    flex-grow: 1;
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 6px 12px;
    color: var(--text-primary);
    font-size: 12px;
  }
  .chat-messages {
    flex-grow: 1;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .message-bubble {
    max-width: 75%;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 13px;
    line-height: 1.5;
  }
  .message-user {
    align-self: flex-end;
    background: linear-gradient(135deg, var(--primary) 0%, #3B82F6 100%);
    color: var(--text-primary);
    border-bottom-right-radius: 2px;
    box-shadow: 0 4px 10px var(--primary-glow);
  }
  .message-ai {
    align-self: flex-start;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    border-bottom-left-radius: 2px;
  }
  
  /* Typing Indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
  }
  .typing-dot {
    width: 6px;
    height: 6px;
    background: var(--text-secondary);
    border-radius: 50%;
    animation: typingBounce 1.4s infinite ease-in-out;
  }
  .typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .typing-dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes typingBounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40% { transform: scale(1.2); opacity: 1; }
  }

  .chat-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 20px;
    background: rgba(11,16,32,0.2);
    border-top: 1px solid var(--border-color);
  }
  .suggestion-btn {
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 11px;
    cursor: pointer;
    transition: var(--transition);
  }
  .suggestion-btn:hover {
    background: var(--primary-glow);
    border-color: var(--primary);
    color: var(--text-primary);
  }

  .chat-input-area {
    display: flex;
    gap: 12px;
    padding: 16px 20px;
    background: rgba(11,16,32,0.4);
    border-top: 1px solid var(--border-color);
  }
  .chat-input {
    flex-grow: 1;
    background: rgba(11,16,32,0.6);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    padding: 10px 16px;
    font-size: 13px;
  }
  .chat-input:focus {
    outline: none;
    border-color: var(--primary);
  }

  /* History Table */
  .history-table-container {
    width: 100%;
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    background: var(--card-bg);
  }
  .history-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 13px;
  }
  .history-table th {
    background: rgba(11,16,32,0.5);
    padding: 16px;
    font-weight: 700;
    color: var(--text-primary);
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-color);
  }
  .history-table td {
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
  }
  .history-table tr:hover {
    background: rgba(255,255,255,0.02);
  }
  .search-filter-container {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .search-input-wrapper {
    position: relative;
    flex-grow: 1;
    max-width: 400px;
  }
  .filter-sort-wrapper {
    display: flex;
    gap: 12px;
  }
  .dropdown-select {
    background: rgba(19, 27, 46, 0.6);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13px;
    cursor: pointer;
    outline: none;
  }
  .dropdown-select:focus {
    border-color: var(--primary);
  }

  /* About layout */
  .about-layout {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 24px;
  }
  .tech-tag-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }
  .tech-tag {
    background: rgba(79, 140, 255, 0.05);
    border: 1px solid rgba(79, 140, 255, 0.15);
    color: var(--primary);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }
  .dev-profile-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
  }
  .dev-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
  }
  .dev-avatar-large {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary) 0%, #a78bfa 100%);
    color: var(--text-primary);
    font-size: 24px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 3px solid var(--border-color);
  }
  .dev-meta {
    display: flex;
    flex-direction: column;
  }
  .dev-title-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
  }
  .dev-subtitle-role {
    font-size: 13px;
    color: var(--text-muted);
  }
  .dev-details-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .dev-detail-item {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
  }
  .dev-detail-item a {
    color: var(--primary);
    text-decoration: none;
  }
  .dev-detail-item a:hover {
    text-decoration: underline;
  }
  .support-form-card {
    height: 100%;
  }

  .success-banner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    text-align: center;
  }
  .success-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--success-glow);
    color: var(--success);
    font-size: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
    border: 2px solid rgba(34,197,94,0.3);
  }

  /* Responsive Design */
  @media (max-width: 1024px) {
    .main-content {
      padding: 24px;
    }
    .grid-2, .about-layout, .prep-layout {
      grid-template-columns: 1fr;
    }
    .prep-layout {
      max-height: none;
    }
    .question-list-pane {
      max-height: 250px;
    }
  }

  @media (max-width: 768px) {
    .sidebar {
      width: var(--sidebar-collapsed-width);
      padding: 24px 8px;
    }
    .sidebar .logo-text, .sidebar .user-info, .sidebar .lang-switcher-container, .sidebar .nav-item span:not(.nav-icon) {
      display: none;
    }
    .main-content {
      margin-left: var(--sidebar-collapsed-width);
    }
    .sidebar.collapsed {
      width: 0;
      padding: 0;
      overflow: hidden;
      border-right: none;
    }
    .main-content.expanded {
      margin-left: 0;
    }
    .page-title {
      font-size: 24px;
    }
  }

  /* Additional Interview Prep Cards */
  .prep-categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
  }
  .prep-category-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    cursor: pointer;
    transition: var(--transition);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    min-height: 200px;
  }
  .prep-category-card:hover {
    border-color: var(--primary);
    box-shadow: 0 8px 30px rgba(79, 140, 255, 0.15);
    transform: translateY(-4px);
  }
  .prep-category-icon {
    font-size: 40px;
    margin-bottom: 12px;
    color: var(--primary);
  }
  .prep-category-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: var(--text-primary);
    margin-bottom: 6px;
  }
  .prep-category-count {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 20px;
  }

  @media print {
    body {
      background: #ffffff !important;
      color: #000000 !important;
    }
    .sidebar, .nav-menu, .sidebar-footer, .api-key-config, .chat-input-area, .suggestion-btn, .lang-switcher-container, button {
      display: none !important;
    }
    .main-content {
      margin-left: 0 !important;
      padding: 0 !important;
      width: 100% !important;
    }
    .glass-card {
      background: none !important;
      border: 1px solid #e2e8f0 !important;
      box-shadow: none !important;
      color: #000000 !important;
      page-break-inside: avoid;
    }
    .page-title, h1, h2, h3, h4, span, div, p {
      color: #000000 !important;
      background: none !important;
      -webkit-text-fill-color: initial !important;
    }
    .pill-badge {
      border: 1px solid #cbd5e1 !important;
      color: #000000 !important;
      background: #f1f5f9 !important;
    }
  }

  /* Resume Builder Styles */
  .resume-builder-page {
    display: flex;
    flex-direction: column;
    gap: 24px;
    padding-bottom: 40px;
  }
  .builder-layout {
    display: flex;
    gap: 24px;
    min-height: calc(100vh - 200px);
    align-items: flex-start;
  }
  .builder-editor-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 20px;
    overflow-y: auto;
    max-height: calc(100vh - 160px);
    padding-right: 8px;
  }
  .builder-preview-pane {
    flex: 1.2;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
    max-height: calc(100vh - 160px);
    align-items: center;
    position: sticky;
    top: 0;
    padding-right: 4px;
  }
  .preview-controls {
    display: flex;
    gap: 12px;
    width: 100%;
    flex-wrap: wrap;
    background: rgba(19, 27, 46, 0.4);
    border: 1px solid var(--border-color);
    padding: 12px 16px;
    border-radius: 12px;
    align-items: center;
  }
  .resume-paper {
    background: #ffffff;
    color: #1e293b;
    width: 100%;
    max-width: 800px;
    min-height: 1050px;
    padding: 44px;
    border-radius: 4px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    position: relative;
    margin: 0 auto;
    box-sizing: border-box;
    text-align: left;
  }
  .resume-paper, .resume-paper div, .resume-paper span, .resume-paper p, .resume-paper h1, .resume-paper h2, .resume-paper h3, .resume-paper h4, .resume-paper li, .resume-paper strong {
    color: #1e293b !important;
    background: transparent !important;
  }
  .resume-paper h1 {
    font-family: 'Space Grotesk', sans-serif;
  }
  .resume-paper h2, .resume-paper h3, .resume-paper h4 {
    font-family: inherit;
  }
  
  /* Scrollbar override for editor and preview panes */
  .builder-editor-pane::-webkit-scrollbar, .builder-preview-pane::-webkit-scrollbar {
    width: 6px;
  }
  .builder-editor-pane::-webkit-scrollbar-track, .builder-preview-pane::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.01);
  }
  .builder-editor-pane::-webkit-scrollbar-thumb, .builder-preview-pane::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.1);
    border-radius: 3px;
  }
  .builder-editor-pane::-webkit-scrollbar-thumb:hover, .builder-preview-pane::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.25);
  }

  /* Responsive Design for Resume Builder */
  @media (max-width: 1024px) {
    .builder-layout {
      flex-direction: column;
      min-height: auto;
    }
    .builder-editor-pane, .builder-preview-pane {
      max-height: none;
      overflow-y: visible;
      width: 100%;
    }
  }

  @media print {
    body {
      background: #ffffff !important;
      color: #000000 !important;
    }
    .sidebar, .nav-menu, .sidebar-footer, .api-key-config, .chat-input-area, .suggestion-btn, .lang-switcher-container, button, .main-content > div:not(.resume-builder-page), .builder-editor-pane, .preview-controls, .page-header, .page-subtitle, .page-title {
      display: none !important;
    }
    .main-content {
      margin-left: 0 !important;
      padding: 0 !important;
      width: 100% !important;
    }
    .resume-paper {
      box-shadow: none !important;
      border: none !important;
      padding: 0 !important;
      margin: 0 !important;
      width: 100% !important;
      min-height: 0 !important;
    }
  }
`;


// Initial Mock Demo Results
const MOCK_ANALYSIS = {
  fileName: "resume_john_doe_senior_java_developer.pdf",
  atsScore: 78.5,
  skillMatchScore: 83.33,
  semanticScore: 73.67,
  allSkills: ["Java", "Spring Boot", "React", "SQL", "PostgreSQL", "AWS", "Docker", "Git", "Python", "Kubernetes"],
  matchedSkills: ["Java", "Spring Boot", "SQL", "AWS", "Docker", "Git"],
  missingSkills: ["React", "Kubernetes", "Python"],
  categorizedSkills: {
    languages: ["Java", "Python"],
    frameworks: ["Spring Boot", "React"],
    databases: ["SQL", "PostgreSQL"],
    cloud: ["AWS", "Docker", "Kubernetes"],
    "ml/ai": [],
    tools: ["Git"]
  },
  candidateInfo: {
    email: "john.doe@example.com",
    phone: "+1 (555) 019-2834",
    experience: "8 Years"
  },
  questions: [
    "Explain the difference between a list and a tuple in Python, and when would you use each?",
    "What is the difference between HashMap, HashTable, and ConcurrentHashMap in Java?",
    "Explain garbage collection in Java. What are the different generations in the Java heap memory?",
    "Explain Dependency Injection and Inversion of Control (IoC) in Spring Boot.",
    "Compare Amazon S3, EBS, and EFS. In what scenarios would you choose one over the others?",
    "What are IAM Roles and IAM Policies in AWS? Explain the principle of least privilege.",
    "What is the difference between a Docker image and a Docker container? Explain copy-on-write.",
    "Explain the differences between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN with examples."
  ],
  recommendedRoles: [
    { role: "Java Developer", matchPercentage: 92 },
    { role: "Software Engineer", matchPercentage: 89 },
    { role: "Web Designing", matchPercentage: 84 },
    { role: "Data Scientist", matchPercentage: 78 },
    { role: "DevOps Engineer", matchPercentage: 75 },
    { role: "Project Manager", matchPercentage: 68 },
    { role: "Consultant", matchPercentage: 62 },
    { role: "Systems Administrator", matchPercentage: 55 }
  ]
};

// Custom SVG Radar Chart for Skill Distribution
function RadarChart({ categorizedSkills }) {
  const categories = [
    { key: 'languages', label: 'Languages' },
    { key: 'frameworks', label: 'Frameworks' },
    { key: 'databases', label: 'Databases' },
    { key: 'cloud', label: 'Cloud' },
    { key: 'ml/ai', label: 'AI/ML' },
    { key: 'tools', label: 'Tools' }
  ];

  const size = 200;
  const center = size / 2;
  const rMax = 70;

  // Calculate matching scores for categories based on number of detected items
  const scores = categories.map(cat => {
    const list = categorizedSkills[cat.key] || [];
    const count = list.length;
    return Math.min(100, count * 20); // 5+ skills = 100%
  });

  // Generate grid points for concentric hexagons
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];
  const gridPolygons = gridLevels.map(level => {
    return categories.map((_, i) => {
      const angle = (i * Math.PI) / 3 - Math.PI / 2;
      const r = rMax * level;
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      return `${x},${y}`;
    }).join(' ');
  });

  // Calculate candidate points
  const candidatePoints = categories.map((_, i) => {
    const angle = (i * Math.PI) / 3 - Math.PI / 2;
    const r = rMax * (scores[i] / 100);
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return `${x},${y}`;
  }).join(' ');

  // Calculate axis lines
  const axes = categories.map((cat, i) => {
    const angle = (i * Math.PI) / 3 - Math.PI / 2;
    const x = center + rMax * Math.cos(angle);
    const y = center + rMax * Math.sin(angle);
    
    // Label offset
    const lx = center + (rMax + 18) * Math.cos(angle);
    const ly = center + (rMax + 10) * Math.sin(angle) + 3;
    
    return { x1: center, y1: center, x2: x, y2: y, lx, ly, label: cat.label };
  });

  return (
    <div style={{ display: 'flex', justifyContent: 'center', margin: '10px 0' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Grid lines */}
        {gridPolygons.map((poly, idx) => (
          <polygon key={idx} points={poly} className="radar-grid" />
        ))}
        
        {/* Axes */}
        {axes.map((axis, idx) => (
          <g key={idx}>
            <line x1={axis.x1} y1={axis.y1} x2={axis.x2} y2={axis.y2} className="radar-axis" />
            <text x={axis.lx} y={axis.ly} className="radar-label">{axis.label}</text>
          </g>
        ))}

        {/* Data polygon */}
        {candidatePoints && (
          <>
            <polygon points={candidatePoints} className="radar-area" />
            {categories.map((_, i) => {
              const angle = (i * Math.PI) / 3 - Math.PI / 2;
              const r = rMax * (scores[i] / 100);
              const x = center + r * Math.cos(angle);
              const y = center + r * Math.sin(angle);
              return (
                <circle key={i} cx={x} cy={y} r="3" className="radar-point" />
              );
            })}
          </>
        )}
      </svg>
    </div>
  );
}

// Helper: Initials generator
function getInitials(email, fileName) {
  if (email && email !== "Not Provided" && email.includes("@")) {
    const name = email.split("@")[0];
    if (name.length > 1) {
      return name.substring(0, 2).toUpperCase();
    }
  }
  if (fileName) {
    const cleaned = fileName.replace(/[^a-zA-Z]/g, '');
    if (cleaned.length > 1) {
      return cleaned.substring(0, 2).toUpperCase();
    }
  }
  return "JD";
}

// Helper: Resume strength tier classifier
function getResumeStrength(score) {
  if (score >= 76) return { label: "Outstanding", class: "badge-neon-green" };
  if (score >= 60) return { label: "Competitive", class: "badge-neon-cyan" };
  if (score >= 50) return { label: "Adequate", class: "badge-neon-yellow" };
  return { label: "Needs Work", class: "badge-neon-red" };
}

// Helper: Dynamic score styling selector
function getScoreColors(score) {
  if (score >= 76) return { color: "#10B981", glow: "rgba(16, 185, 129, 0.4)", textClass: "text-green" };
  if (score >= 51) return { color: "#F59E0B", glow: "rgba(245, 158, 11, 0.4)", textClass: "text-yellow" };
  return { color: "#EF4444", glow: "rgba(239, 68, 68, 0.4)", textClass: "text-red" };
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// Helper: Animated number count up effect
const AnimatedNumber = ({ value }) => {
  const [displayVal, setDisplayVal] = React.useState(0);
  React.useEffect(() => {
    let start = 0;
    const end = parseInt(value, 10);
    if (isNaN(end)) {
      setDisplayVal(value);
      return;
    }
    if (end === 0) {
      setDisplayVal(0);
      return;
    }
    const duration = 800; // ms
    const increment = end / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= end) {
        setDisplayVal(end);
        clearInterval(timer);
      } else {
        setDisplayVal(Math.floor(current));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [value]);
  return <span>{displayVal}</span>;
};

export default function App() {
  const [activePage, setActivePage] = useState('upload');
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  
  // Current analysis data state, starts empty.
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // Score Simulator State
  const [simulatedAddedSkills, setSimulatedAddedSkills] = useState([]);
  useEffect(() => {
    setSimulatedAddedSkills([]);
  }, [analysisResult]);
  
  // Interview Question panel states
  const [expandedQuestionId, setExpandedQuestionId] = useState(null);
  const [questionCategoryTab, setQuestionCategoryTab] = useState('Technical');
  
  // User Authentication
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [simulatedEmail, setSimulatedEmail] = useState('');

  // History state
  const [historyList, setHistoryList] = useState([]);
  
  // Tab selector for Interview Prep
  const [prepTab, setPrepTab] = useState('technical');
  
  // Mock Interview Simulator State
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [candidateAnswer, setCandidateAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationResult, setEvaluationResult] = useState(null);

  // Chat state for AI Coach
  const [apiKey, setApiKey] = useState(localStorage.getItem('anthropic_key') || '');
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: "Hello! I am your AI Coach. I can help you practice for your mock interviews. Ask me a technical question, or let's start a mock interview!" }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // Multiple Language State (English, Hindi, Tamil)
  const [lang, setLang] = useState(localStorage.getItem('app_lang') || 'en');

  // Collapsible sidebar state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // History search, filter, and sort states
  const [historySearchQuery, setHistorySearchQuery] = useState('');
  const [historyFilter, setHistoryFilter] = useState('all');
  const [historySort, setHistorySort] = useState('newest');

  // Selected Category on Interview Prep page
  const [selectedPrepCategory, setSelectedPrepCategory] = useState(null);

  // Help & Support Form State (Empty by default)
  const [supportName, setSupportName] = useState('');
  const [supportEmail, setSupportEmail] = useState('');
  const [supportMessage, setSupportMessage] = useState('');
  const [supportSubmitted, setSupportSubmitted] = useState(false);

  // AI Resume Builder States
  const [resumePersonalInfo, setResumePersonalInfo] = useState({
    name: '',
    title: '',
    email: '',
    phone: '',
    website: '',
    linkedin: '',
    github: ''
  });

  const [resumeSummary, setResumeSummary] = useState('');

  const [resumeExperience, setResumeExperience] = useState([]);

  const [resumeProjects, setResumeProjects] = useState([]);

  const [resumeEducation, setResumeEducation] = useState([]);

  const [resumeSkills, setResumeSkills] = useState('');

  const [resumeTemplate, setResumeTemplate] = useState('modern'); // 'modern', 'slate', 'creative', 'classic'
  const [resumeAccentColor, setResumeAccentColor] = useState('#4F8CFF'); // default primary
  const [resumeFontFamily, setResumeFontFamily] = useState('sans-serif'); // 'sans-serif', 'serif', 'monospace'
  const [resumeFontSize, setResumeFontSize] = useState(13); // font size in px
  const [aiEnhancingSummary, setAiEnhancingSummary] = useState(false);
  const [aiEnhancingExpIdx, setAiEnhancingExpIdx] = useState(null); // index of experience item being enhanced
  const [aiEnhancingProjIdx, setAiEnhancingProjIdx] = useState(null); // index of project item being enhanced
  const [aiSuggestingSkills, setAiSuggestingSkills] = useState(false);

  const enhanceResumeSection = async (type, currentText, index = null) => {
    // Start loading
    if (type === 'summary') setAiEnhancingSummary(true);
    else if (type === 'experience') setAiEnhancingExpIdx(index);
    else if (type === 'project') setAiEnhancingProjIdx(index);
    else if (type === 'skills') setAiSuggestingSkills(true);

    if (apiKey) {
      // Direct Claude API Call
      try {
        let prompt = "";
        if (type === 'summary') {
          prompt = `Enhance the following professional summary to be highly professional, impactful, and optimized for an ATS. Focus on accomplishments and tech leadership. Avoid placeholders or template structures. Return ONLY the rewritten text without comments, conversational intro/outros, or markdown blocks:\n\n${currentText}`;
        } else if (type === 'experience' || type === 'project') {
          prompt = `Enhance the following job/project description to use strong action verbs (e.g. spearheaded, designed, optimized) and focus on quantitative results and technical impacts. Format it as bullet points starting with '• '. Return ONLY the rewritten bullets without introductory remarks, markdown wraps, or meta-comments:\n\n${currentText}`;
        } else if (type === 'skills') {
          prompt = `Based on these current skills: "${currentText}", suggest a list of 5-8 highly relevant, missing technical keywords or tools that a modern senior developer should include. Return ONLY the final comma-separated list of suggested skills, no other text:\n\n${currentText}`;
        }

        const response = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'dangerouslyAllowBrowser': 'true'
          },
          body: JSON.stringify({
            model: 'claude-3-5-sonnet-20241022',
            max_tokens: 500,
            system: "You are an expert resume optimization coach. You rewrite sections to make them ATS-friendly and professional.",
            messages: [{ role: 'user', content: prompt }]
          })
        });

        if (response.ok) {
          const data = await response.json();
          let result = data.content[0].text.trim();
          // Remove potential wrapping quotes or markdown backticks
          result = result.replace(/^["'`]|["'`]$/g, '').replace(/```(markdown)?/g, '').trim();

          if (type === 'summary') {
            setResumeSummary(result);
          } else if (type === 'experience') {
            const updated = [...resumeExperience];
            updated[index].description = result;
            setResumeExperience(updated);
          } else if (type === 'project') {
            const updated = [...resumeProjects];
            updated[index].description = result;
            setResumeProjects(updated);
          } else if (type === 'skills') {
            setResumeSkills(prev => prev ? `${prev}, ${result}` : result);
          }
        } else {
          // Fallback to local rewrite if API fails
          runLocalEnhance(type, currentText, index);
        }
      } catch (err) {
        runLocalEnhance(type, currentText, index);
      } finally {
        setAiEnhancingSummary(false);
        setAiEnhancingExpIdx(null);
        setAiEnhancingProjIdx(null);
        setAiSuggestingSkills(false);
      }
    } else {
      // Local simulator rewrite
      setTimeout(() => {
        runLocalEnhance(type, currentText, index);
        setAiEnhancingSummary(false);
        setAiEnhancingExpIdx(null);
        setAiEnhancingProjIdx(null);
        setAiSuggestingSkills(false);
      }, 1200);
    }
  };

  const runLocalEnhance = (type, currentText, index) => {
    if (type === 'summary') {
      const enhanced = currentText
        .replace(/\bworked on\b/gi, 'spearheaded and architected')
        .replace(/\bhelped with\b/gi, 'collaborated on orchestrating')
        .replace(/\bresponsible for\b/gi, 'drove operational excellence and took ownership of')
        .replace(/\bmanaged\b/gi, 'orchestrated and directed');
      const suffix = " Leveraged modern software paradigms to deliver highly scalable, secure, and fault-tolerant system solutions, maximizing business delivery and technical metrics.";
      setResumeSummary(enhanced.endsWith('.') ? enhanced + suffix : enhanced + '.' + suffix);
    } else if (type === 'experience' || type === 'project') {
      let bullets = currentText.split('\n').map(b => b.trim()).filter(Boolean);
      let enhancedBullets = bullets.map(b => {
        let clean = b.replace(/^[•\-\*\s]+/, '');
        clean = clean
          .replace(/\bhelped\b/gi, 'collaborated in architecting')
          .replace(/\bworked on\b/gi, 'spearheaded development of')
          .replace(/\bmanaged\b/gi, 'orchestrated and scaled')
          .replace(/\bmade\b/gi, 'engineered and optimized')
          .replace(/\bfixed\b/gi, 'debugged and streamlined')
          .replace(/\bused\b/gi, 'leveraged');
        
        // Add simulated metrics
        if (!clean.includes('%') && !clean.includes('x') && !clean.includes('times')) {
          if (clean.toLowerCase().includes('perf') || clean.toLowerCase().includes('speed') || clean.toLowerCase().includes('api')) {
            clean += ", yielding a 35% reduction in latency overheads.";
          } else if (clean.toLowerCase().includes('deploy') || clean.toLowerCase().includes('pipeline')) {
            clean += ", improving release cycles by 40% and team velocity.";
          } else if (clean.toLowerCase().includes('team') || clean.toLowerCase().includes('developer')) {
            clean += ", resulting in a 2x boost to operational team throughput.";
          } else {
            clean += ", driving key metrics and platform availability.";
          }
        }
        return `• ${clean}`;
      });
      const result = enhancedBullets.join('\n');
      if (type === 'experience') {
        const updated = [...resumeExperience];
        updated[index].description = result;
        setResumeExperience(updated);
      } else {
        const updated = [...resumeProjects];
        updated[index].description = result;
        setResumeProjects(updated);
      }
    } else if (type === 'skills') {
      const suggestions = ['Redux Toolkit', 'FastAPI', 'OAuth2.0', 'Redis Cache', 'TypeScript', 'Jest/Enzyme', 'Terraform (IaC)'];
      // Filter out existing skills
      const currentLower = currentText.toLowerCase();
      const filtered = suggestions.filter(s => !currentLower.includes(s.toLowerCase()));
      if (filtered.length > 0) {
        setResumeSkills(prev => prev ? `${prev}, ${filtered.join(', ')}` : filtered.join(', '));
      }
    }
  };

  const chatBottomRef = useRef(null);
  const recognitionRef = useRef(null);

  const getCompletenessScore = (info) => {
    let score = 0.0;
    if (info?.email && info.email !== "Not Provided") {
      score += 40.0;
    }
    if (info?.phone && info.phone !== "Not Provided") {
      score += 40.0;
    }
    if (info?.experience && info.experience !== "Entry Level" && info.experience !== "Not Provided") {
      score += 20.0;
    } else {
      score += 10.0;
    }
    return score;
  };

  // Calculate simulated score
  const getSimulatedAtsScore = () => {
    if (!analysisResult) return 0;
    const baseAtsScore = analysisResult.atsScore;
    const baseMatchedCount = analysisResult.matchedSkills.length;
    const missingSkillsList = analysisResult.missingSkills || [];
    
    // Filter to get unique skill names from prioritized lists if object
    const missingNames = missingSkillsList.map(s => typeof s === 'object' && s !== null ? s.name : s);
    const totalRequiredCount = baseMatchedCount + missingNames.length;
    
    if (totalRequiredCount === 0) return baseAtsScore;
    
    // Matched skills + simulated added skills count
    const newMatchedCount = baseMatchedCount + simulatedAddedSkills.length;
    const newSkillMatchScore = (newMatchedCount / totalRequiredCount) * 100;
    
    // Formula: (0.70 * Skill Match Score) + (0.20 * Semantic Similarity Score) + (0.10 * Profile Completeness Score)
    const semanticScore = analysisResult.semanticScore || 60;
    const completenessScore = getCompletenessScore(analysisResult.candidateInfo);
    
    const projectedScore = (0.70 * newSkillMatchScore) + (0.20 * semanticScore) + (0.10 * completenessScore);
    return Math.round(projectedScore * 10) / 10;
  };

  const toggleSimulatedSkill = (name) => {
    setSimulatedAddedSkills(prev => 
      prev.includes(name) ? prev.filter(s => s !== name) : [...prev, name]
    );
  };

  const getProjectedScoreForSkill = (name) => {
    if (!analysisResult) return "+0";
    const baseMatchedCount = analysisResult.matchedSkills.length;
    const missingSkillsList = analysisResult.missingSkills || [];
    const missingNames = missingSkillsList.map(s => typeof s === 'object' && s !== null ? s.name : s);
    const totalRequiredCount = baseMatchedCount + missingNames.length;
    if (totalRequiredCount === 0) return "+0";
    const increase = (0.70 * (1 / totalRequiredCount)) * 100;
    return `+${(Math.round(increase * 10) / 10)}`;
  };

  const getCareerAssistantData = () => {
    if (!analysisResult) return null;
    if (analysisResult.careerAssistantData) return analysisResult.careerAssistantData;
    
    // Generate fallback data dynamically based on the history item's available fields
    const baseMatchedCount = analysisResult.matchedSkills?.length || 0;
    const missingSkillsList = analysisResult.missingSkills || [];
    const missingNames = missingSkillsList.map(s => typeof s === 'object' && s !== null ? s.name : s);
    const totalRequiredCount = baseMatchedCount + missingNames.length;
    const skillMatchScore = totalRequiredCount > 0 ? (baseMatchedCount / totalRequiredCount) * 100 : 70;
    
    const sectionScores = {
      skills: Math.round(skillMatchScore),
      projects: 70,
      experience: Math.round(analysisResult.completenessScore || 65),
      education: 85,
      achievements: 50,
      certifications: 40
    };
    
    return {
      sectionScores,
      weakestSection: "certifications",
      aiInsights: {
        strengths: ["Good structural layout.", "Identified key technical skills."],
        weaknesses: ["Fewer quantified metrics and business achievements.", "Lacks certifications for target stack."],
        highestImpactImprovement: missingNames.length > 0 ? `Add ${missingNames[0]} experience to projects.` : "Quantify project accomplishments.",
        recommendedNextAction: missingNames.length > 0 ? `Build a mini-project using ${missingNames[0]}.` : "Include metrics like 'reduced latency by 20%'"
      },
      resumeOptimizer: {
        weakSections: ["Certifications", "Achievements"],
        improvements: ["Use the STAR method: Action-Result framework to rewrite bullet points.", "Add GitHub and demo links for projects."],
        rewrittenBullets: [
          {
            original: "Worked on python code and databases.",
            rewritten: "Architected scalable Python backend systems, optimizing query performance by 35%."
          }
        ],
        keywordsToAdd: missingNames.slice(0, 4)
      },
      learningRoadmap: {
        plan7Days: missingNames.length > 0 ? [`Understand core concepts of ${missingNames[0]}.`] : ["Review system design patterns."],
        plan30Days: missingNames.length > 0 ? [`Build a functional CRUD app with ${missingNames[0]}.`] : ["Build a distributed cache proxy."],
        plan60Days: ["Deploy projects to public cloud.", "Write technical documentation."]
      },
      careerPaths: [
        { role: "Software Engineer", matchPercentage: Math.round(analysisResult.atsScore || 70), salaryRange: "$95,000 - $140,000", marketDemand: "High" }
      ],
      skillGap: {
        "Programming": { current: analysisResult.matchedSkills?.slice(0, 3) || [], required: ["Java", "Python", "SQL"], gapPercentage: 30 }
      },
      jobReadinessIndex: Math.round(analysisResult.atsScore || 70),
      detailedQuestions: [
        {
          id: 1,
          question: "How do you handle scalability and performance optimization in your stack?",
          expectedAnswer: "Explain caching, horizontal scaling, database indexing, and query optimization.",
          keyConcepts: ["Scalability", "System Design"],
          difficulty: "Medium",
          category: "Technical"
        }
      ]
    };
  };

  // Helper Translate Function
  const t = (key) => {
    return TRANSLATIONS[lang][key] || TRANSLATIONS['en'][key] || key;
  };

  const handleLangChange = (newLang) => {
    setLang(newLang);
    localStorage.setItem('app_lang', newLang);
  };

  // Inject CSS styles into the DOM
  useEffect(() => {
    const styleEl = document.createElement('style');
    styleEl.innerHTML = styles;
    document.head.appendChild(styleEl);
    return () => {
      document.head.removeChild(styleEl);
    };
  }, []);

  // Initialize Google Sign-in on Mount
  useEffect(() => {
    const loadGoogleGsi = () => {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.body.appendChild(script);
      
      script.onload = () => {
        if (window.google) {
          window.google.accounts.id.initialize({
            client_id: '999999999999-mockclientid.apps.googleusercontent.com',
            callback: handleGoogleLoginCallback,
          });
          const btnEl = document.getElementById('google-signin-btn');
          if (btnEl) {
            window.google.accounts.id.renderButton(btnEl, {
              theme: 'outline',
              size: 'large',
              width: 280
            });
          }
        }
      };
    };

    if (!user) {
      loadGoogleGsi();
    }
  }, [user]);

  // Poll backend health status
  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/health`);
      if (response.ok) {
        const data = await response.json();
        if (data.backend === 'UP') {
          setIsBackendOnline(true);
          return;
        }
      }
      setIsBackendOnline(false);
    } catch {
      setIsBackendOnline(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch History on load and update
  const fetchHistory = async () => {
    try {
      const headers = {};
      if (user) {
        headers['X-User-Id'] = user.id.toString();
      }
      const response = await fetch(`${API_BASE_URL}/api/resume/history`, { headers });
      if (response.ok) {
        const data = await response.json();
        setHistoryList(data);
      }
    } catch (err) {
      console.error("Failed to load database history", err);
    }
  };

  useEffect(() => {
    if (activePage === 'history' && user) {
      fetchHistory();
    }
  }, [activePage, user]);

  // Scroll to bottom of chat when a message is added
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isTyping]);

  // Google Authentication verify
  const handleGoogleLoginCallback = async (response) => {
    const credential = response.credential;
    await verifyAndLogin(credential);
  };

  const handleSimulatedLoginSubmit = async (e) => {
    e.preventDefault();
    if (!simulatedEmail.trim()) return;
    await verifyAndLogin('mock_' + simulatedEmail.trim());
  };

  const verifyAndLogin = async (token) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/google-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('auth_user', JSON.stringify(userData));
      } else {
        alert("Google Authentication verify failed on Backend.");
      }
    } catch (err) {
      console.error(err);
      const mockEmail = token.startsWith('mock_') ? token.substring(5) : 'demo@gmail.com';
      const userData = {
        id: 999,
        email: mockEmail,
        name: mockEmail.split('@')[0].toUpperCase(),
        pictureUrl: 'https://lh3.googleusercontent.com/a/default-user=s96-c',
        createdAt: new Date().toISOString()
      };
      setUser(userData);
      localStorage.setItem('auth_user', JSON.stringify(userData));
    }
  };

  const handleSignOut = () => {
    setUser(null);
    localStorage.removeItem('auth_user');
  };

  // Drag and Drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        setSelectedFile(file);
      } else {
        alert("Only PDF files are supported.");
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.name.endsWith(".pdf")) {
        setSelectedFile(file);
      } else {
        alert("Only PDF files are supported.");
      }
    }
  };

  // Submit file for analysis
  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setUploading(true);

    if (!isBackendOnline) {
      setTimeout(() => {
        setAnalysisResult({
          ...MOCK_ANALYSIS,
          fileName: selectedFile.name,
          atsScore: Math.round((70 + Math.random() * 25) * 10) / 10,
        });
        setUploading(false);
        setActivePage('ats');
      }, 2000);
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('jobDescription', jobDescription);

    const headers = {};
    if (user) {
      headers['X-User-Id'] = user.id.toString();
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/analyze`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const formattedData = {
          id: data.id,
          fileName: data.fileName,
          atsScore: data.atsScore,
          skillMatchScore: data.skillMatchScore,
          semanticScore: data.semanticScore,
          beforeAtsScore: data.beforeAtsScore,
          confidenceScore: data.confidenceScore,
          jdAvailable: data.jdAvailable,
          allSkills: data.allSkills || JSON.parse(data.allSkillsJson || '[]'),
          matchedSkills: data.matchedSkills || JSON.parse(data.matchedSkillsJson || '[]'),
          missingSkills: data.missingSkills || JSON.parse(data.missingSkillsJson || '[]'),
          categorizedSkills: data.categorizedSkills || {
            languages: [], frameworks: [], databases: [], cloud: [], "ml/ai": [], tools: []
          },
          candidateInfo: data.candidateInfo || { email: "Not Provided", phone: "Not Provided", experience: "Entry Level" },
          questions: data.questions || [],
          recommendedRoles: data.recommendedRoles || ["Software Engineer", "Backend Developer", "Frontend Developer"],
          careerAssistantData: data.careerAssistantData
        };
        setAnalysisResult(formattedData);
        if (formattedData.questions && formattedData.questions.length > 0) {
          setActiveQuestion(formattedData.questions[0]);
          setCandidateAnswer('');
          setEvaluationResult(null);
        }
        setUploading(false);
        setActivePage('ats');
      } else {
        alert("Error during server analysis. Check backend logs.");
        setUploading(false);
      }
    } catch (err) {
      console.error(err);
      alert("Network error connecting to backend. Falling back to mock demo.");
      setUploading(false);
    }
  };

  // Switch to History item
  const handleLoadHistoryItem = (item) => {
    const formattedData = {
      id: item.id,
      fileName: item.fileName,
      atsScore: item.atsScore,
      skillMatchScore: item.skillMatchScore,
      semanticScore: item.semanticScore,
      beforeAtsScore: item.beforeAtsScore,
      confidenceScore: item.confidenceScore,
      jdAvailable: item.jobDescription ? true : false,
      allSkills: JSON.parse(item.allSkillsJson || '[]'),
      matchedSkills: JSON.parse(item.matchedSkillsJson || '[]'),
      missingSkills: JSON.parse(item.missingSkillsJson || '[]'),
      categorizedSkills: {
        languages: [], frameworks: [], databases: [], cloud: [], "ml/ai": [], tools: []
      },
      candidateInfo: { email: "Not Provided", phone: "Not Provided", experience: "Not Provided" },
      questions: [],
      recommendedRoles: ["Software Engineer", "Backend Developer", "Consultant", "Data Scientist", "DevOps Engineer", "Project Manager"]
    };
    setAnalysisResult(formattedData);
    setActivePage('ats');
  };

  // Web Speech API Voice Transcription
  const startRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Web Speech API is not supported in this browser. Please type your response.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsRecording(true);
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        }
      }
      setCandidateAnswer(prev => prev + finalTranscript);
    };

    recognition.onerror = (e) => {
      console.error("Speech recognition error: ", e);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  };

  // Submit Mock Answer for Evaluation
  const handleEvaluateAnswer = async () => {
    if (!candidateAnswer.trim() || !activeQuestion) return;

    setEvaluating(true);
    setEvaluationResult(null);

    if (!isBackendOnline) {
      setTimeout(() => {
        setEvaluationResult({
          score: 8.5,
          correctness: "The candidate shows an understanding of the concepts and details core libraries.",
          missing: "Missed details regarding thread safety profiles and low-level JVM memory overhead.",
          modelAnswer: "A model answer should explain concurrency controls, memory segmentation, and complexity profiles.",
          tips: [
            "Elaborate on internal thread synchronization mechanisms.",
            "Use STAR structured answering pattern.",
            "Keep definitions direct and give real-life usage scenarios."
          ]
        });
        setEvaluating(false);
      }, 1500);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/evaluate-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: activeQuestion,
          answer: candidateAnswer,
          skills: analysisResult?.allSkills || []
        })
      });
      if (response.ok) {
        const data = await response.json();
        setEvaluationResult(data);
      } else {
        alert("Evaluation call failed.");
      }
    } catch (e) {
      console.error(e);
      alert("Error reaching evaluation endpoint. Loading simulated response.");
      setEvaluationResult({
        score: 7.8,
        correctness: "Accurately definitions for primary terms.",
        missing: "Could mention memory foot prints and scalability configurations.",
        modelAnswer: "Provide a direct response outlining definition, mechanics and context.",
        tips: ["Highlight technical architecture in the answer.", "Add real-world implementation details."]
      });
    } finally {
      setEvaluating(false);
    }
  };

  // Help & Support Form Submit
  const handleSupportFormSubmit = (e) => {
    e.preventDefault();
    if (!supportMessage.trim()) return;
    setSupportSubmitted(true);
  };

  const handleResetSupportForm = () => {
    setSupportMessage('');
    setSupportSubmitted(false);
  };

  // Save Anthropic API Key
  const handleApiKeyChange = (e) => {
    setApiKey(e.target.value);
    localStorage.setItem('anthropic_key', e.target.value);
  };

  // Send message to AI Coach
  const handleSendMessage = async (customText) => {
    const text = customText || chatInput;
    if (!text.trim()) return;

    if (!customText) setChatInput('');

    const updatedMessages = [...chatMessages, { role: 'user', content: text }];
    setChatMessages(updatedMessages);
    setIsTyping(true);

    if (!apiKey) {
      setTimeout(() => {
        let aiResponse = "I am ready to guide you. To get actual interview simulation responses, please enter your Anthropic API Key above. ";
        if (text.toLowerCase().includes("mock interview") || text.toLowerCase().includes("start mock")) {
          aiResponse += "\n\nLet's start! Here is your first question: 'Can you tell me about yourself and your experience with " + (analysisResult?.allSkills?.[0] || 'software engineering') + "?'";
        } else if (text.toLowerCase().includes("technical question") || text.toLowerCase().includes("ask me")) {
          aiResponse += "\n\nSure, here is a common technical query: 'How does garbage collection work in a runtime environment, and what are the performance impacts of manual memory management?'";
        } else {
          aiResponse += "\n\nI can answer questions regarding: " + (analysisResult?.allSkills || []).join(", ") + ". How would you like me to assist you?";
        }
        setChatMessages([...updatedMessages, { role: 'assistant', content: aiResponse }]);
        setIsTyping(false);
      }, 1500);
      return;
    }

    try {
      const systemPrompt = `You are a helpful AI Interview Coach assisting a candidate. The candidate has these skills: ${(analysisResult?.allSkills || []).join(', ')}. Offer constructive feedback, coding questions, behavioral advice (using STAR method), and simulate realistic tech interviews. Keep your responses clear, helpful, and concise.`;

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
          'dangerouslyAllowBrowser': 'true'
        },
        body: JSON.stringify({
          model: 'claude-3-5-sonnet-20241022',
          max_tokens: 1024,
          system: systemPrompt,
          messages: updatedMessages.map(m => ({ role: m.role, content: m.content }))
        })
      });

      if (response.ok) {
        const data = await response.json();
        const aiResponse = data.content[0].text;
        setChatMessages([...updatedMessages, { role: 'assistant', content: aiResponse }]);
      } else {
        const errData = await response.json();
        setChatMessages([...updatedMessages, { role: 'assistant', content: `API Error: ${errData.error?.message || response.statusText}. Ensure CORS is bypassed, or check API key.` }]);
      }
    } catch (err) {
      setChatMessages([...updatedMessages, { role: 'assistant', content: "CORS blocks direct browser calls to Anthropic's API. Please run a proxy or use the simulator fallback." }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Helper colors for Score Ring
  const getScoreColorClass = (score) => {
    if (score >= 75) return 'score-green';
    if (score >= 50) return 'score-yellow';
    return 'score-red';
  };

  const getScoreTextClass = (score) => {
    if (score >= 75) return 'text-green';
    if (score >= 50) return 'text-yellow';
    return 'text-red';
  };

  // If user not authenticated, present the beautiful lock login page
  if (!user) {
    return (
      <div className="login-screen">
        <div className="login-card">
          <div className="login-logo">⚡</div>
          <h2 className="login-title">Interview AI</h2>
          <p className="login-desc">Sign in with Google or use Gmail Demo Bypass to get started.</p>
          
          <div className="google-signin-btn-container">
            <div id="google-signin-btn"></div>
          </div>

          <div className="divider">Or Simulated Bypass</div>

          <form className="mock-login-form" onSubmit={handleSimulatedLoginSubmit}>
            <div className="form-group" style={{ marginBottom: '12px' }}>
              <input 
                type="email" 
                className="input-field" 
                placeholder="Enter your Gmail address (e.g. john@gmail.com)" 
                value={simulatedEmail} 
                onChange={(e) => setSimulatedEmail(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn" style={{ width: '100%' }}>
              🔑 Simulated Gmail Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <div className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="logo-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="logo-icon">⚡</div>
            {!isSidebarCollapsed && <div className="logo-text">INTERVIEW AI</div>}
          </div>
          <button className="sidebar-toggle-btn" onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}>
            {isSidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        {/* Dynamic Language Switcher Widget inside sidebar (English, Hindi, Tamil) */}
        {!isSidebarCollapsed && (
          <div className="lang-switcher-container">
            <span className="lang-label">Lang:</span>
            <div className="lang-buttons">
              <button className={`lang-btn ${lang === 'en' ? 'active' : ''}`} onClick={() => handleLangChange('en')}>EN</button>
              <button className={`lang-btn ${lang === 'hi' ? 'active' : ''}`} onClick={() => handleLangChange('hi')}>HI</button>
              <button className={`lang-btn ${lang === 'ta' ? 'active' : ''}`} onClick={() => handleLangChange('ta')}>TA</button>
            </div>
          </div>
        )}

        {/* User profile details at top of sidebar */}
        <div className="user-sidebar-profile">
          <img className="user-avatar" src={user.pictureUrl} alt="Avatar" />
          {!isSidebarCollapsed && (
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <span className="user-email">{user.email}</span>
              <button className="signout-btn" onClick={handleSignOut}>Sign out</button>
            </div>
          )}
        </div>

        <ul className="nav-menu">
          <li className={`nav-item ${activePage === 'upload' ? 'active' : ''}`} onClick={() => setActivePage('upload')}>
            <span className="nav-icon" title={t('uploadResume')}><Upload size={18} /></span>
            {!isSidebarCollapsed && <span>{t('uploadResume')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'ats' ? 'active' : ''}`} onClick={() => setActivePage('ats')}>
            <span className="nav-icon" title={t('atsResults')}><BarChart2 size={18} /></span>
            {!isSidebarCollapsed && <span>{t('atsResults')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'skills' ? 'active' : ''}`} onClick={() => setActivePage('skills')}>
            <span className="nav-icon" title={t('skillsAnalysis')}><Code size={18} /></span>
            {!isSidebarCollapsed && <span>{t('skillsAnalysis')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'prep' ? 'active' : ''}`} onClick={() => {
            setActivePage('prep');
            if (analysisResult && analysisResult.questions && analysisResult.questions.length > 0 && !activeQuestion) {
              setActiveQuestion(analysisResult.questions[0]);
            }
          }}>
            <span className="nav-icon" title={t('interviewPrep')}><HelpCircle size={18} /></span>
            {!isSidebarCollapsed && <span>{t('interviewPrep')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'coach' ? 'active' : ''}`} onClick={() => setActivePage('coach')}>
            <span className="nav-icon" title={t('aiCoach')}><MessageSquare size={18} /></span>
            {!isSidebarCollapsed && <span>{t('aiCoach')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'builder' ? 'active' : ''}`} onClick={() => setActivePage('builder')}>
            <span className="nav-icon" title={t('resumeBuilder')}><FileText size={18} /></span>
            {!isSidebarCollapsed && <span>{t('resumeBuilder')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'history' ? 'active' : ''}`} onClick={() => setActivePage('history')}>
            <span className="nav-icon" title={t('history')}><Clock size={18} /></span>
            {!isSidebarCollapsed && <span>{t('history')}</span>}
          </li>
          <li className={`nav-item ${activePage === 'about' ? 'active' : ''}`} onClick={() => setActivePage('about')}>
            <span className="nav-icon" title={t('aboutSupport')}><Info size={18} /></span>
            {!isSidebarCollapsed && <span>{t('aboutSupport')}</span>}
          </li>
        </ul>

        <div className="sidebar-footer">
          <div className="status-badge">
            <div className={`status-indicator ${isBackendOnline ? 'online' : ''}`}></div>
            {!isSidebarCollapsed && <span>{isBackendOnline ? t('backendOnline') : t('backendOffline')}</span>}
          </div>
        </div>
      </div>

      {/* Main Content Pane */}
      <div className={`main-content ${isSidebarCollapsed ? 'expanded' : ''}`}>
        
        {/* PAGE 1: UPLOAD RESUME */}
        {activePage === 'upload' && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.3 }}
          >
            <div className="page-header">
              <h1 className="page-title">{t('uploadTitle')}</h1>
              <p className="page-subtitle">{t('uploadSubtitle')}</p>
            </div>

            <div style={{ maxWidth: '640px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Upload Zone & Form */}
              <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div 
                  className="upload-zone"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => document.getElementById('file-input').click()}
                  style={{ position: 'relative' }}
                >
                  <input 
                    type="file" 
                    id="file-input" 
                    accept=".pdf" 
                    style={{ display: 'none' }} 
                    onChange={handleFileChange} 
                  />
                  <motion.div 
                    animate={{ y: [0, -8, 0] }}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                    className="upload-icon"
                    style={{ fontSize: '48px', color: '#4F8CFF', marginBottom: '16px' }}
                  >
                    📤
                  </motion.div>
                  <div className="upload-text" style={{ fontSize: '16px', fontWeight: '600', color: '#fff', marginBottom: '8px' }}>
                    {t('dragDropText')}
                  </div>
                  <div className="upload-subtext" style={{ fontSize: '13px', color: '#B8C1D9' }}>
                    {t('clickBrowseText')}
                  </div>
                  
                  {selectedFile && (
                    <motion.div 
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="selected-file-badge"
                      style={{ marginTop: '16px', display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(79, 140, 255, 0.1)', border: '1px solid rgba(79, 140, 255, 0.2)', padding: '6px 12px', borderRadius: '20px', color: '#4F8CFF', fontSize: '13px' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedFile(null);
                      }}
                    >
                      <span>📄 {selectedFile.name}</span>
                      <span style={{ cursor: 'pointer', fontWeight: 'bold', marginLeft: '4px' }}>✕</span>
                    </motion.div>
                  )}
                </div>

                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', color: '#B8C1D9', letterSpacing: '0.5px' }}>
                    {t('jobDescLabel')}
                  </label>
                  <textarea 
                    className="form-textarea" 
                    placeholder={t('jobDescPlaceholder')}
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    style={{ minHeight: '140px', background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '8px', padding: '12px', fontSize: '14px' }}
                  />
                </div>

                {uploading ? (
                  <div className="upload-progress-container">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', color: '#B8C1D9' }}>
                      <span>Analyzing Resume...</span>
                      <span className="spinner" style={{ width: '16px', height: '16px', border: '2px solid rgba(79,140,255,0.1)', borderTop: '2px solid #4F8CFF', borderRadius: '50%', display: 'inline-block' }}></span>
                    </div>
                    <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', marginTop: '8px', overflow: 'hidden' }}>
                      <motion.div 
                        initial={{ width: "0%" }}
                        animate={{ width: "95%" }}
                        transition={{ duration: 2, ease: "easeOut" }}
                        className="progress-bar-fill"
                        style={{ height: '100%', background: '#4F8CFF' }}
                      />
                    </div>
                    <p style={{ fontSize: '11px', color: '#64748B', marginTop: '6px', fontStyle: 'italic' }}>{t('analyzingText')}</p>
                  </div>
                ) : (
                  <button 
                    className="btn" 
                    disabled={!selectedFile}
                    onClick={handleAnalyze}
                    style={{ width: '100%', padding: '14px' }}
                  >
                    🚀 {t('analyzeBtn')}
                  </button>
                )}
              </div>

              <div className="supported-formats-badge">
                <span style={{ fontWeight: '600' }}>Supported Format</span>
                <span className="badge-neon badge-neon-green" style={{ fontSize: '10px' }}>PDF Only</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* PAGE 2: ATS RESULTS */}
        {activePage === 'ats' && !analysisResult && (
          <div className="empty-state-card" style={{ padding: '40px', textAlign: 'center', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.15)', margin: '20px auto', maxWidth: '600px' }}>
            <span style={{ fontSize: '48px', display: 'block', marginBottom: '20px' }}>📊</span>
            <h2 style={{ fontSize: '24px', color: '#fff', marginBottom: '10px' }}>No Scorecard Data Available</h2>
            <p style={{ color: '#aaa', margin: '0 auto 20px auto', lineHeight: '1.6' }}>Please upload a resume on the <strong>Upload Resume</strong> tab to analyze it and view your ATS Scorecard.</p>
            <button className="analyze-btn" onClick={() => setActivePage('upload')} style={{ cursor: 'pointer', display: 'inline-block', width: 'auto', padding: '12px 30px' }}>Go to Upload</button>
          </div>
        )}

        {activePage === 'ats' && analysisResult && (() => {
          const saasData = getCareerAssistantData();
          const simulatedScore = getSimulatedAtsScore();
          const missingSkillsList = analysisResult.missingSkills || [];
          const missingNames = missingSkillsList.map(s => typeof s === 'object' && s !== null ? s.name : s);

          // Categorize missing skills by priority
          const highPriority = missingNames.slice(0, 3);
          const medPriority = missingNames.slice(3, 6);
          const lowPriority = missingNames.slice(6);



          return (
            <motion.div 
              initial={{ opacity: 0, y: 15 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.5 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '40px' }}
            >
              {/* Header section with modern title and file name */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
                <div>
                  <h1 className="page-title" style={{ fontSize: '28px', fontWeight: '800', fontFamily: "'Space Grotesk', sans-serif", background: 'linear-gradient(to right, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', margin: 0 }}>
                    AI Career Assistant Dashboard
                  </h1>
                  <p className="page-subtitle" style={{ fontSize: '13px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', margin: 0 }}>
                    <FileText size={14} /> File: <span style={{ color: '#e2e8f0', fontWeight: '600' }}>{analysisResult.fileName}</span>
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    className="btn btn-outline" 
                    onClick={() => window.print()}
                    style={{ padding: '8px 16px', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '12px', borderRadius: '10px' }}
                  >
                    📥 Download ATS Report
                  </button>
                  {analysisResult.jdAvailable ? (
                    <div className="badge-neon badge-neon-cyan" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      <Target size={12} /> SBERT Context Match
                    </div>
                  ) : (
                    <div className="badge-neon badge-neon-purple" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      <Compass size={12} /> Standard Profile Match
                    </div>
                  )}
                </div>
              </div>

              {/* ==================================================
                  SECTION 1 — HERO DASHBOARD
                  ================================================== */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px' }}>
                {/* ATS Score Card */}
                <div className="premium-glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '110px', position: 'relative' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>ATS Match Score</span>
                    <TrendingUp size={14} style={{ color: 'var(--primary)' }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: '800', color: '#ffffff' }}>
                      <AnimatedNumber value={simulatedScore} />%
                    </div>
                    {simulatedScore !== analysisResult.atsScore && (
                      <span style={{ fontSize: '10px', color: 'var(--success)', fontWeight: '700' }}>(Base: {analysisResult.atsScore}%)</span>
                    )}
                  </div>
                </div>

                {/* Confidence Card */}
                <div className="premium-glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '110px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Confidence Score</span>
                    <Activity size={14} style={{ color: '#22d3ee' }} />
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: '800', color: '#22d3ee' }}>
                    <AnimatedNumber value={analysisResult.confidenceScore !== undefined ? analysisResult.confidenceScore : 85} />%
                  </div>
                </div>

                {/* Job Readiness Card */}
                <div className="premium-glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '110px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Job Readiness</span>
                    <Award size={14} style={{ color: '#a78bfa' }} />
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: '800', color: '#a78bfa' }}>
                    <AnimatedNumber value={saasData?.jobReadinessIndex || 70} />%
                  </div>
                </div>

                {/* Skills Found Card */}
                <div className="premium-glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '110px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Skills Found</span>
                    <Cpu size={14} style={{ color: '#34d399' }} />
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: '800', color: '#34d399' }}>
                    <AnimatedNumber value={analysisResult.allSkills?.length || 0} />
                  </div>
                </div>

                {/* Matched Count Card */}
                <div className="premium-glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '110px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Matched Skills</span>
                    <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--success)' }}>
                    <AnimatedNumber value={analysisResult.matchedSkills?.length || 0} />
                  </div>
                </div>

                {/* Missing Count Card */}
                <div className="premium-glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '110px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Missing Skills</span>
                    <ShieldAlert size={14} style={{ color: 'var(--danger)' }} />
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--danger)' }}>
                    <AnimatedNumber value={missingNames.length} />
                  </div>
                </div>
              </div>

              {/* ==================================================
                  SECTION 2 — MAIN INSIGHTS
                  ================================================== */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
                {/* Left: Large ATS Score Circle */}
                <div className="premium-glass-card" style={{ flexGrow: 2, flexBasis: '60%', padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '24px', marginTop: 0 }}>
                    ATS Readiness Assessment
                  </h3>

                  <div className="radial-score-container" style={{ '--ring-glow': getScoreColors(simulatedScore).glow, margin: '10px 0' }}>
                    <svg className="radial-score-svg" width="160" height="160">
                      <circle className="radial-circle-bg" cx="80" cy="80" r="70" />
                      <motion.circle 
                        className="radial-circle-val"
                        cx="80" 
                        cy="80" 
                        r="70" 
                        stroke={getScoreColors(simulatedScore).color}
                        strokeDasharray="440"
                        initial={{ strokeDashoffset: 440 }}
                        animate={{ strokeDashoffset: 440 - (440 * simulatedScore) / 100 }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                      />
                    </svg>
                    <div className="radial-score-text">
                      <span className="radial-score-num" style={{ fontSize: '38px', fontWeight: '800' }}>{simulatedScore}%</span>
                      <span className="radial-score-label" style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {simulatedScore >= 76 ? 'Excellent Match' : simulatedScore >= 50 ? 'Strong Match' : 'Needs Work'}
                      </span>
                    </div>
                  </div>

                  {/* Below Circle: Progress Bar */}
                  <div style={{ width: '100%', maxWidth: '380px', marginTop: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      <span>ATS READINESS INDEX</span>
                      <span>{simulatedScore}%</span>
                    </div>
                    <div className="section-score-bar-bg" style={{ height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${simulatedScore}%` }}
                        transition={{ duration: 1 }}
                        className="section-score-bar-fill" 
                        style={{ height: '100%', background: getScoreColors(simulatedScore).color, borderRadius: '4px' }}
                      />
                    </div>
                  </div>
                </div>

                {/* Right: AI Quick Summary Card */}
                <div className="premium-glass-card" style={{ flexGrow: 1, flexBasis: '35%', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', margin: 0 }}>
                    AI Quick Summary
                  </h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '4px' }}>
                    <div>
                      <span style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Key Strengths</span>
                      <div className="badge-neon badge-neon-green" style={{ display: 'inline-flex', fontSize: '11px', padding: '4px 10px', borderRadius: '8px' }}>
                        {saasData?.aiInsights?.strengths?.[0] || 'Strong technology stack alignment'}
                      </div>
                    </div>

                    <div>
                      <span style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Profile Rating</span>
                      <div className={`badge-neon ${getResumeStrength(simulatedScore).class}`} style={{ display: 'inline-flex', fontSize: '11px', padding: '4px 10px', borderRadius: '8px' }}>
                        {getResumeStrength(simulatedScore).label}
                      </div>
                    </div>

                    <div>
                      <span style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Experience Level</span>
                      <div className="badge-neon badge-neon-purple" style={{ display: 'inline-flex', fontSize: '11px', padding: '4px 10px', borderRadius: '8px' }}>
                        {analysisResult.candidateInfo?.experience || 'Not Provided'}
                      </div>
                    </div>

                    <div>
                      <span style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Recommended Role</span>
                      <div className="badge-neon badge-neon-cyan" style={{ display: 'inline-flex', fontSize: '11px', padding: '4px 10px', borderRadius: '8px' }}>
                        {saasData?.careerPaths?.[0]?.role || 'Software Engineer'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* ==================================================
                  SECTION 3 — SKILLS ANALYSIS
                  ================================================== */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
                {/* Matched Skills Card */}
                <div className="premium-glass-card" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '1px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CheckCircle size={15} style={{ color: 'var(--success)' }} /> Matched Skills
                    </h3>
                    <span className="badge-neon badge-neon-green" style={{ fontSize: '10px' }}>
                      {analysisResult.matchedSkills?.length || 0} Found
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                    {analysisResult.matchedSkills && analysisResult.matchedSkills.length > 0 ? (
                      analysisResult.matchedSkills.map(skill => (
                        <span key={skill} className="skill-pill-badge skill-pill-matched">
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>No matching profile keywords.</span>
                    )}
                  </div>
                </div>

                {/* Missing Skills Card & Simulator */}
                <div className="premium-glass-card" style={{ padding: '24px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '1px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <ShieldAlert size={15} style={{ color: 'var(--danger)' }} /> Missing Skills (Click to Simulate)
                    </h3>
                    <span className="badge-neon badge-neon-red" style={{ fontSize: '10px' }}>
                      {missingNames.length} Missing
                    </span>
                  </div>

                  {missingNames.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {/* High Priority */}
                      {highPriority.length > 0 && (
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                            <span className="priority-chip priority-chip-high">High Priority</span>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {highPriority.map(name => {
                              const added = simulatedAddedSkills.includes(name);
                              return (
                                <span 
                                  key={name} 
                                  className={`skill-pill-badge ${added ? 'skill-pill-matched' : 'skill-pill-missing'}`}
                                  onClick={() => toggleSimulatedSkill(name)}
                                  style={{ cursor: 'pointer' }}
                                  title="Click to toggle simulation"
                                >
                                  {added ? '✓' : '+'} {name}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Medium Priority */}
                      {medPriority.length > 0 && (
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                            <span className="priority-chip priority-chip-medium">Medium Priority</span>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {medPriority.map(name => {
                              const added = simulatedAddedSkills.includes(name);
                              return (
                                <span 
                                  key={name} 
                                  className={`skill-pill-badge ${added ? 'skill-pill-matched' : 'skill-pill-missing'}`}
                                  onClick={() => toggleSimulatedSkill(name)}
                                  style={{ cursor: 'pointer' }}
                                  title="Click to toggle simulation"
                                >
                                  {added ? '✓' : '+'} {name}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Low Priority */}
                      {lowPriority.length > 0 && (
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                            <span className="priority-chip priority-chip-low">Low Priority</span>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {lowPriority.map(name => {
                              const added = simulatedAddedSkills.includes(name);
                              return (
                                <span 
                                  key={name} 
                                  className={`skill-pill-badge ${added ? 'skill-pill-matched' : 'skill-pill-missing'}`}
                                  onClick={() => toggleSimulatedSkill(name)}
                                  style={{ cursor: 'pointer' }}
                                  title="Click to toggle simulation"
                                >
                                  {added ? '✓' : '+'} {name}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <span style={{ fontSize: '12px', color: 'var(--text-success)', fontStyle: 'italic' }}>Profile perfectly optimized.</span>
                  )}
                </div>
              </div>

              {/* ==================================================
                  SECTION 4 — AI IMPROVEMENT CENTER
                  ================================================== */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' }}>
                {/* Resume Strengths */}
                <div className="premium-glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '2px solid #22C55E' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle size={18} style={{ color: 'var(--success)' }} />
                    <h4 style={{ fontSize: '14px', fontWeight: '800', margin: 0, color: '#fff' }}>Resume Strengths</h4>
                  </div>
                  <ul style={{ paddingLeft: '16px', color: 'var(--text-secondary)', fontSize: '12.5px', margin: 0, display: 'flex', flexDirection: 'column', gap: '6px', lineHeight: '1.4' }}>
                    {saasData?.aiInsights?.strengths.map((str, idx) => (
                      <li key={idx}>{str}</li>
                    )) || <li>Strong structural layout.</li>}
                  </ul>
                </div>

                {/* Critical Gaps */}
                <div className="premium-glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '2px solid #EF4444' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldAlert size={18} style={{ color: 'var(--danger)' }} />
                    <h4 style={{ fontSize: '14px', fontWeight: '800', margin: 0, color: '#fff' }}>Critical Gaps</h4>
                  </div>
                  <ul style={{ paddingLeft: '16px', color: 'var(--text-secondary)', fontSize: '12.5px', margin: 0, display: 'flex', flexDirection: 'column', gap: '6px', lineHeight: '1.4' }}>
                    {saasData?.aiInsights?.weaknesses.map((weak, idx) => (
                      <li key={idx}>{weak}</li>
                    )) || <li>Lacks quantified metrics.</li>}
                  </ul>
                </div>

                {/* Next Best Action */}
                <div className="premium-glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '2px solid #F59E0B' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={18} style={{ color: 'var(--warning)' }} />
                    <h4 style={{ fontSize: '14px', fontWeight: '800', margin: 0, color: '#fff' }}>Next Best Action</h4>
                  </div>
                  <div style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.5', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div>
                      <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>Highest Impact: </span>
                      {saasData?.aiInsights?.highestImpactImprovement}
                    </div>
                    <div>
                      <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>Action Item: </span>
                      {saasData?.aiInsights?.recommendedNextAction}
                    </div>
                  </div>
                </div>
              </div>

              {/* ==================================================
                  SECTION 5 — RESUME SECTION ANALYSIS
                  ================================================== */}
              <div className="premium-glass-card" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '20px', marginTop: 0 }}>
                  Resume Section Analysis
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  {saasData?.sectionScores && Object.entries(saasData.sectionScores)
                    .filter(([sec]) => ['skills', 'projects', 'experience', 'education', 'certifications'].includes(sec))
                    .map(([sec, val]) => {
                      const isWeak = val < 60;
                      const isExcellent = val >= 80;
                      const status = isExcellent ? 'Excellent' : isWeak ? 'Needs Work' : 'Good';
                      const statusColor = isExcellent ? 'var(--success)' : isWeak ? 'var(--danger)' : 'var(--warning)';

                      return (
                        <div key={sec} style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '700', textTransform: 'capitalize', color: '#fff' }}>
                            <span>{sec}</span>
                            <span>{val}%</span>
                          </div>
                          
                          <div className="section-score-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div className="section-score-bar-fill" style={{ width: `${val}%`, height: '100%', background: statusColor, borderRadius: '3px' }} />
                          </div>

                          <div style={{ fontSize: '10px', fontWeight: '800', color: statusColor, textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: '2px' }}>
                            {status}
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>



              {/* ==================================================
                  SECTION 7 — CAREER RECOMMENDATIONS
                  ================================================== */}
              <div className="premium-glass-card" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '20px', marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Compass size={15} style={{ color: '#60a5fa' }} /> AI Career Recommendations
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                  {saasData?.careerPaths?.map((path, idx) => (
                    <div key={idx} style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <h4 style={{ fontSize: '14px', fontWeight: '800', margin: 0, color: '#fff' }}>{path.role}</h4>
                      
                      <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11.5px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>Match</span>
                          <span className="badge-neon badge-neon-cyan" style={{ fontWeight: '700' }}>{path.matchPercentage}% Match</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>Salary</span>
                          <strong style={{ color: '#fff' }}>{path.salaryRange}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>Demand</span>
                          <span className="badge-neon badge-neon-green" style={{ fontSize: '10px' }}>{path.marketDemand}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* ==================================================
                  SECTION 8 — LEARNING ROADMAP
                  ================================================== */}
              <div className="premium-glass-card" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '24px', marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <TrendingUp size={15} style={{ color: '#22C55E' }} /> AI Learning Timeline Roadmap
                </h3>

                <div className="vertical-timeline">
                  {/* Week 1 */}
                  <div className="vertical-timeline-item">
                    <div className="vertical-timeline-dot" />
                    <div className="vertical-timeline-title">Week 1: Foundations & Core Technologies</div>
                    <div className="vertical-timeline-content">
                      <ul style={{ paddingLeft: '14px', margin: '4px 0 0 0', listStyleType: 'circle' }}>
                        {saasData?.learningRoadmap?.plan7Days?.map((item, i) => (
                          <li key={i}>{item}</li>
                        )) || <li>Focus on core backend/frontend gaps.</li>}
                      </ul>
                    </div>
                  </div>

                  {/* Week 2 */}
                  <div className="vertical-timeline-item">
                    <div className="vertical-timeline-dot" style={{ borderColor: 'var(--warning)' }} />
                    <div className="vertical-timeline-title">Week 2: Build & Apply integrations</div>
                    <div className="vertical-timeline-content">
                      <ul style={{ paddingLeft: '14px', margin: '4px 0 0 0', listStyleType: 'circle' }}>
                        <li>Set up local sandbox models and CRUD databases.</li>
                        <li>Integrate high-priority mock interview components into custom projects.</li>
                      </ul>
                    </div>
                  </div>

                  {/* Month 1 */}
                  <div className="vertical-timeline-item">
                    <div className="vertical-timeline-dot" style={{ borderColor: '#a78bfa' }} />
                    <div className="vertical-timeline-title">Month 1: Advanced Project Engineering</div>
                    <div className="vertical-timeline-content">
                      <ul style={{ paddingLeft: '14px', margin: '4px 0 0 0', listStyleType: 'circle' }}>
                        {saasData?.learningRoadmap?.plan30Days?.map((item, i) => (
                          <li key={i}>{item}</li>
                        )) || <li>Optimize databases and implement scalability caching.</li>}
                      </ul>
                    </div>
                  </div>

                  {/* Month 2 */}
                  <div className="vertical-timeline-item">
                    <div className="vertical-timeline-dot" style={{ borderColor: '#34d399' }} />
                    <div className="vertical-timeline-title">Month 2: Scale, Deployment & Testing</div>
                    <div className="vertical-timeline-content">
                      <ul style={{ paddingLeft: '14px', margin: '4px 0 0 0', listStyleType: 'circle' }}>
                        {saasData?.learningRoadmap?.plan60Days?.map((item, i) => (
                          <li key={i}>{item}</li>
                        )) || <li>Deploy to staging environments and write full integration unit suites.</li>}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

            </motion.div>
          );
        })()}\n


        {/* PAGE 3: SKILLS ANALYSIS */}


        {/* PAGE 3: SKILLS ANALYSIS */}
        {activePage === 'skills' && !analysisResult && (
          <div className="empty-state-card" style={{ padding: '40px', textAlign: 'center', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.15)', margin: '20px auto', maxWidth: '600px' }}>
            <span style={{ fontSize: '48px', display: 'block', marginBottom: '20px' }}>🔍</span>
            <h2 style={{ fontSize: '24px', color: '#fff', marginBottom: '10px' }}>No Skills Analysis Available</h2>
            <p style={{ color: '#aaa', margin: '0 auto 20px auto', lineHeight: '1.6' }}>Please upload a resume on the <strong>Upload Resume</strong> tab to analyze and view your extracted skills breakdown.</p>
            <button className="analyze-btn" onClick={() => setActivePage('upload')} style={{ cursor: 'pointer', display: 'inline-block', width: 'auto', padding: '12px 30px' }}>Go to Upload</button>
          </div>
        )}

        {activePage === 'skills' && analysisResult && (
          <div>
            <div className="page-header">
              <h1 className="page-title">{t('skillsTitle')}</h1>
              <p className="page-subtitle">{t('skillsSubtitle')}</p>
            </div>

            <div className="grid-2">
              {Object.entries(analysisResult.categorizedSkills || {}).map(([category, list]) => (
                <div key={category} className="category-card">
                  <div className="category-title">
                    <span style={{ textTransform: 'capitalize' }}>{category === 'ml/ai' ? 'ML & AI' : category.replace('&', ' & ')}</span>
                    <span className="category-count">{list.length} Found</span>
                  </div>
                  <div className="chips-container">
                    {list.length > 0 ? (
                      list.map((skill) => (
                        <span key={skill} className="chip chip-violet">{skill}</span>
                      ))
                    ) : (
                      <span style={{ fontSize: '12px', color: '#64748B', fontStyle: 'italic' }}>{t('noSkillsDetected')}</span>
                    )}
                  </div>
                </div>
              ))}
              
              {(!analysisResult.categorizedSkills || Object.keys(analysisResult.categorizedSkills).length === 0) && (
                <div className="category-card" style={{ gridColumn: 'span 2' }}>
                  <div className="category-title">
                    <span>{t('allSkillsDetected')}</span>
                    <span className="category-count">{analysisResult.allSkills.length} {t('totalSkills')}</span>
                  </div>
                  <div className="chips-container">
                    {analysisResult.allSkills.map((skill) => (
                      <span key={skill} className="chip chip-violet">{skill}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* PAGE 4: INTERVIEW PREP & MOCK SIMULATOR */}
        {activePage === 'prep' && !analysisResult && (
          <div className="empty-state-card" style={{ padding: '40px', textAlign: 'center', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.15)', margin: '20px auto', maxWidth: '600px' }}>
            <span style={{ fontSize: '48px', display: 'block', marginBottom: '20px' }}>❓</span>
            <h2 style={{ fontSize: '24px', color: '#fff', marginBottom: '10px' }}>No Mock Interview Questions</h2>
            <p style={{ color: '#aaa', margin: '0 auto 20px auto', lineHeight: '1.6' }}>Please upload a resume on the <strong>Upload Resume</strong> tab to automatically generate relevant mock interview questions.</p>
            <button className="analyze-btn" onClick={() => setActivePage('upload')} style={{ cursor: 'pointer', display: 'inline-block', width: 'auto', padding: '12px 30px' }}>Go to Upload</button>
          </div>
        )}

        {activePage === 'prep' && analysisResult && (() => {
          const saasData = getCareerAssistantData();
          const techQuestions = analysisResult.questions || [];
          const behavioralQuestions = [
            "Describe a time when you had to resolve a severe technical disagreement within your engineering team. What approach did you take?",
            "Describe a challenging software bug or design problem that you had to tackle under a tight deadline. How did you organize your investigation?",
            "Tell me about a project that failed or missed its key goals. What did you learn and how did it influence your subsequent engineering practices?",
            "How do you handle balancing new product feature requests with paying down technical debt in your codebase?"
          ];
          const projectQuestions = saasData?.detailedQuestions?.filter(q => q.category === 'Project-Based').map(q => q.question) || [
            "How would you integrate a new messaging bus architecture into an existing production stack?",
            "Detail the scalability bottlenecks you faced in your recent project deployment and how you tackled them."
          ];
          const hrQuestions = saasData?.detailedQuestions?.filter(q => q.category === 'HR').map(q => q.question) || [
            "Why do you want to join this role, and how do you align with our technological roadmap?",
            "Where do you see yourself in 5 years? Describe your career growth plans."
          ];

          const categories = [
            { id: 'technical', title: 'Technical', icon: '💻', count: techQuestions.length, list: techQuestions },
            { id: 'behavioral', title: 'Behavioral', icon: '⭐', count: behavioralQuestions.length, list: behavioralQuestions },
            { id: 'project', title: 'Project-Based', icon: '🚀', count: projectQuestions.length, list: projectQuestions },
            { id: 'hr', title: 'HR & Cultural', icon: '🤝', count: hrQuestions.length, list: hrQuestions }
          ];

          return (
            <motion.div 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
            >
              <div className="page-header">
                <h1 className="page-title">{t('prepTitle')}</h1>
                <p className="page-subtitle">{t('prepSubtitle')}</p>
              </div>

              {selectedPrepCategory === null ? (
                /* Category Cards Selection */
                <div className="prep-categories-grid">
                  {categories.map((cat) => (
                    <motion.div 
                      key={cat.id}
                      className="prep-category-card"
                      onClick={() => {
                        setSelectedPrepCategory(cat.id);
                        if (cat.list.length > 0) {
                          setActiveQuestion(cat.list[0]);
                        } else {
                          setActiveQuestion(null);
                        }
                        setCandidateAnswer('');
                        setEvaluationResult(null);
                      }}
                      whileHover={{ scale: 1.03, y: -4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="prep-category-icon">{cat.icon}</div>
                      <div>
                        <h3 className="prep-category-title">{cat.title}</h3>
                        <p className="prep-category-count">{cat.count} Questions Available</p>
                      </div>
                      <button className="btn" style={{ padding: '8px 16px', fontSize: '12px' }}>
                        Start Practice
                      </button>
                    </motion.div>
                  ))}
                </div>
              ) : (
                /* Split Layout for selected category */
                (() => {
                  const currentCategory = categories.find(c => c.id === selectedPrepCategory);
                  const questionsList = currentCategory ? currentCategory.list : [];

                  return (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <button 
                          className="btn btn-outline" 
                          onClick={() => setSelectedPrepCategory(null)}
                          style={{ padding: '8px 16px', fontSize: '12px' }}
                        >
                          ← Back to Categories
                        </button>
                        <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#4F8CFF', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Category: {currentCategory?.title}
                        </span>
                      </div>

                      <div className="prep-layout">
                        <div className="question-list-pane">
                          {questionsList.map((q, idx) => (
                            <div 
                              key={idx} 
                              className={`question-item ${activeQuestion === q ? 'active' : ''}`}
                              onClick={() => {
                                setActiveQuestion(q);
                                setCandidateAnswer('');
                                setEvaluationResult(null);
                              }}
                            >
                              <div className="question-num">{idx + 1}</div>
                              <div className="question-text" title={q}>{q}</div>
                            </div>
                          ))}
                        </div>

                        <div className="simulator-pane">
                          {activeQuestion ? (
                            <div className="card" style={{ marginBottom: 0 }}>
                              <h3 style={{ fontSize: '14px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '12px', color: '#4F8CFF', letterSpacing: '0.5px' }}>
                                {t('activeQuestionLabel')}
                              </h3>
                              <p style={{ fontSize: '15px', lineHeight: 1.6, marginBottom: '20px', color: '#fff' }}>{activeQuestion}</p>
                              
                              <div className="form-group">
                                <label className="form-label">{t('yourResponseLabel')}</label>
                                <textarea 
                                  className="form-textarea"
                                  placeholder={t('responsePlaceholder')}
                                  value={candidateAnswer}
                                  onChange={(e) => setCandidateAnswer(e.target.value)}
                                  style={{ minHeight: '140px', background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '12px' }}
                                />
                                
                                <div className="speech-actions">
                                  {!isRecording ? (
                                    <button className="record-btn" onClick={startRecording}>
                                      {t('recordBtn')}
                                    </button>
                                  ) : (
                                    <button className="record-btn recording" onClick={stopRecording}>
                                      {t('stopBtn')}
                                    </button>
                                  )}
                                  {isRecording && (
                                    <div className="speech-wave">
                                      <span className="speech-bar"></span>
                                      <span className="speech-bar"></span>
                                      <span className="speech-bar"></span>
                                      <span style={{ fontSize: '11px', color: '#EF4444', marginLeft: '6px' }}>Listening...</span>
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                                <button 
                                  className="btn" 
                                  disabled={evaluating || !candidateAnswer.trim()}
                                  onClick={handleEvaluateAnswer}
                                >
                                  {evaluating ? t('evaluatingBtn') : t('evaluateBtn')}
                                </button>
                              </div>

                              {evaluationResult && (
                                <div className="evaluation-card">
                                  <div className="eval-header">
                                    <h4 style={{ color: '#4F8CFF', fontSize: '14px', fontWeight: '700' }}>{t('feedbackTitle')}</h4>
                                    <div className="eval-score-container">
                                      <span style={{ fontSize: '12px', color: '#B8C1D9' }}>{t('scoreText')}:</span>
                                      <div className="eval-score-ring">{evaluationResult.score}/10</div>
                                    </div>
                                  </div>

                                  <div className="eval-section-title">{t('correctPoints')}</div>
                                  <p className="eval-section-content">{evaluationResult.correctness}</p>

                                  <div className="eval-section-title">{t('missingConcepts')}</div>
                                  <p className="eval-section-content">{evaluationResult.missing}</p>

                                  <div className="eval-section-title">{t('tipsImprovement')}</div>
                                  <ul className="tips-list" style={{ marginBottom: '16px', paddingLeft: '16px' }}>
                                    {evaluationResult.tips && evaluationResult.tips.map((tip, i) => (
                                      <li key={i} style={{ marginBottom: '4px' }}>{tip}</li>
                                    ))}
                                  </ul>

                                  <div className="eval-section-title">{t('idealModelAnswer')}</div>
                                  <p className="eval-section-content" style={{ color: '#a78bfa', fontStyle: 'italic', marginBottom: 0 }}>
                                    "{evaluationResult.modelAnswer}"
                                  </p>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748B' }}>
                              {t('selectQuestionPrompt')}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })()
              )}
            </motion.div>
          );
        })()}

        {/* PAGE 5: AI COACH */}
        {activePage === 'coach' && (
          <div>
            <div className="page-header">
              <h1 className="page-title">{t('coachTitle')}</h1>
              <p className="page-subtitle">{t('coachSubtitle')}</p>
            </div>

            <div className="chat-layout" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)', background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', overflow: 'hidden' }}>
              <div className="api-key-config" style={{ padding: '16px 20px', background: 'rgba(11,16,32,0.4)', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Sparkles size={14} style={{ color: 'var(--primary)' }} /> {t('claudeKeyLabel')}
                </span>
                <input 
                  type="password" 
                  className="api-key-input" 
                  placeholder={t('claudePlaceholder')}
                  value={apiKey}
                  onChange={handleApiKeyChange}
                  style={{ flexGrow: 1, background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '8px 12px', color: 'var(--text-primary)', fontSize: '12px' }}
                />
                <span style={{ fontSize: '11px', fontWeight: '600', color: apiKey ? 'var(--success)' : 'var(--warning)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {apiKey ? `✔️ ${t('savedLocal')}` : `⚠️ ${t('simulatorMode')}`}
                </span>
              </div>

              <div className="chat-messages" style={{ flexGrow: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {chatMessages.map((m, idx) => {
                  const isUser = m.role === 'user';
                  return (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      style={{
                        display: 'flex',
                        flexDirection: isUser ? 'row-reverse' : 'row',
                        gap: '12px',
                        alignItems: 'flex-start',
                        alignSelf: isUser ? 'flex-end' : 'flex-start',
                        maxWidth: '80%',
                      }}
                    >
                      {/* Initials Avatar */}
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '10px',
                        background: isUser ? 'linear-gradient(135deg, var(--primary) 0%, #3B82F6 100%)' : 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        fontWeight: '700',
                        fontSize: '11px',
                        boxShadow: '0 4px 10px rgba(0,0,0,0.2)',
                        flexShrink: 0,
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}>
                        {isUser ? 'ME' : 'AI'}
                      </div>

                      {/* Message Card */}
                      <div className="glass-card" style={{
                        padding: '14px 18px',
                        borderRadius: isUser ? '16px 2px 16px 16px' : '2px 16px 16px 16px',
                        background: isUser ? 'rgba(79, 140, 255, 0.08)' : 'rgba(19, 27, 46, 0.65)',
                        border: isUser ? '1px solid rgba(79, 140, 255, 0.2)' : '1px solid var(--border-color)',
                        boxShadow: isUser ? '0 4px 15px rgba(79, 140, 255, 0.05)' : '0 4px 15px rgba(0, 0, 0, 0.2)',
                        position: 'relative',
                      }}>
                        <div style={{
                          fontSize: '10px',
                          color: isUser ? 'var(--primary)' : '#a78bfa',
                          fontWeight: '700',
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                          marginBottom: '4px',
                        }}>
                          {isUser ? 'You' : 'AI Career Coach'}
                        </div>
                        <div style={{
                          color: '#ffffff',
                          fontSize: '13px',
                          lineHeight: '1.6',
                          whiteSpace: 'pre-wrap',
                        }}>
                          {m.content}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
                
                {isTyping && (
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center', alignSelf: 'flex-start' }}>
                    <div style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#fff',
                      fontWeight: '700',
                      fontSize: '11px',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      boxShadow: '0 4px 10px rgba(0,0,0,0.2)',
                    }}>
                      AI
                    </div>
                    <div className="glass-card" style={{ padding: '12px 18px', borderRadius: '2px 16px 16px 16px' }}>
                      <div className="typing-indicator" style={{ display: 'flex', gap: '4px' }}>
                        <div className="typing-dot" style={{ width: '6px', height: '6px', background: 'var(--text-secondary)', borderRadius: '50%', animation: 'typingBounce 1.4s infinite ease-in-out' }}></div>
                        <div className="typing-dot" style={{ width: '6px', height: '6px', background: 'var(--text-secondary)', borderRadius: '50%', animation: 'typingBounce 1.4s infinite ease-in-out', animationDelay: '0.2s' }}></div>
                        <div className="typing-dot" style={{ width: '6px', height: '6px', background: 'var(--text-secondary)', borderRadius: '50%', animation: 'typingBounce 1.4s infinite ease-in-out', animationDelay: '0.4s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Suggestions */}
              <div className="chat-suggestions" style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '12px 20px', background: 'rgba(11,16,32,0.2)', borderTop: '1px solid var(--border-color)' }}>
                <button className="suggestion-btn" onClick={() => handleSendMessage("Ask me a technical question")}>
                  💬 Ask me a technical question
                </button>
                <button className="suggestion-btn" onClick={() => handleSendMessage("Give me a system design question")}>
                  💻 System design question
                </button>
                <button className="suggestion-btn" onClick={() => handleSendMessage("How should I answer using the STAR methodology?")}>
                  ⭐ STAR answer guide
                </button>
                <button className="suggestion-btn" onClick={() => handleSendMessage("What are common interview mistakes?")}>
                  ❌ Common mistakes
                </button>
                <button className="suggestion-btn" onClick={() => handleSendMessage("Start a mock interview")}>
                  🎯 Start mock interview
                </button>
              </div>

              {/* Input bar */}
              <div className="chat-input-area" style={{ display: 'flex', gap: '12px', padding: '16px 20px', background: 'rgba(11,16,32,0.4)', borderTop: '1px solid var(--border-color)', alignItems: 'center' }}>
                <input 
                  type="text" 
                  className="chat-input" 
                  placeholder="Ask Claude a question or type your response here..." 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSendMessage();
                  }}
                  style={{ flexGrow: 1, background: 'rgba(11,16,32,0.6)', border: '1px solid var(--border-color)', borderRadius: '8px', color: 'var(--text-primary)', padding: '10px 16px', fontSize: '13px' }}
                />
                <button className="btn" onClick={() => handleSendMessage()} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                  {t('sendBtn')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* PAGE 8: AI RESUME BUILDER */}
        {activePage === 'builder' && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.3 }}
            className="resume-builder-page"
          >
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h1 className="page-title">{t('resumeBuilder')}</h1>
                <p className="page-subtitle">Draft a highly professional, ATS-optimized resume using our AI assistant and premium styling templates.</p>
              </div>
              <button 
                className="btn" 
                onClick={() => window.print()}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#22C55E', borderColor: '#22C55E' }}
              >
                🖨️ Export / Print PDF
              </button>
            </div>

            <div className="builder-layout">
              {/* Left Column: Form Editor */}
              <div className="builder-editor-pane">
                {/* Accordion 1: Personal Info */}
                <div className="card" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '15px', color: '#fff', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                    👤 Personal Information
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '11px' }}>Full Name</label>
                      <input 
                        type="text" 
                        value={resumePersonalInfo.name} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, name: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '11px' }}>Target Job Title</label>
                      <input 
                        type="text" 
                        value={resumePersonalInfo.title} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, title: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '11px' }}>Email Address</label>
                      <input 
                        type="email" 
                        value={resumePersonalInfo.email} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, email: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '11px' }}>Phone Number</label>
                      <input 
                        type="text" 
                        value={resumePersonalInfo.phone} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, phone: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '11px' }}>Website Portfolio</label>
                      <input 
                        type="text" 
                        value={resumePersonalInfo.website} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, website: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '11px' }}>LinkedIn Profile</label>
                      <input 
                        type="text" 
                        value={resumePersonalInfo.linkedin} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, linkedin: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                    <div className="form-group" style={{ gridColumn: 'span 2' }}>
                      <label className="form-label" style={{ fontSize: '11px' }}>GitHub Profile</label>
                      <input 
                        type="text" 
                        value={resumePersonalInfo.github} 
                        onChange={(e) => setResumePersonalInfo({...resumePersonalInfo, github: e.target.value})}
                        style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                      />
                    </div>
                  </div>
                </div>

                {/* Accordion 2: Professional Summary */}
                <div className="card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                    <h3 style={{ fontSize: '15px', color: '#fff', margin: 0 }}>
                      ✍️ Professional Summary
                    </h3>
                    <button 
                      className="btn" 
                      onClick={() => enhanceResumeSection('summary', resumeSummary)}
                      disabled={aiEnhancingSummary}
                      style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      {aiEnhancingSummary ? '✨ Improving...' : '✨ AI Enhance Summary'}
                    </button>
                  </div>
                  <textarea 
                    value={resumeSummary} 
                    onChange={(e) => setResumeSummary(e.target.value)}
                    style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '12px', width: '100%', minHeight: '100px', fontSize: '13px', lineHeight: '1.5' }}
                  />
                </div>

                {/* Accordion 3: Work Experience */}
                <div className="card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                    <h3 style={{ fontSize: '15px', color: '#fff', margin: 0 }}>
                      💼 Work Experience
                    </h3>
                    <button 
                      className="btn"
                      onClick={() => setResumeExperience([...resumeExperience, { company: '', role: '', duration: '', description: '' }])}
                      style={{ fontSize: '11px', padding: '4px 10px' }}
                    >
                      ➕ Add Experience
                    </button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {resumeExperience.map((exp, idx) => (
                      <div key={idx} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '16px', position: 'relative' }}>
                        <button 
                          onClick={() => setResumeExperience(resumeExperience.filter((_, i) => i !== idx))}
                          style={{ position: 'absolute', top: '10px', right: '10px', border: 'none', background: 'none', color: '#EF4444', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px' }}
                          title="Remove Entry"
                        >
                          ✕
                        </button>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                          <div className="form-group">
                            <label className="form-label" style={{ fontSize: '11px' }}>Company</label>
                            <input 
                              type="text" 
                              value={exp.company} 
                              onChange={(e) => {
                                const updated = [...resumeExperience];
                                updated[idx].company = e.target.value;
                                setResumeExperience(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                          <div className="form-group">
                            <label className="form-label" style={{ fontSize: '11px' }}>Role Title</label>
                            <input 
                              type="text" 
                              value={exp.role} 
                              onChange={(e) => {
                                const updated = [...resumeExperience];
                                updated[idx].role = e.target.value;
                                setResumeExperience(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                          <div className="form-group" style={{ gridColumn: 'span 2' }}>
                            <label className="form-label" style={{ fontSize: '11px' }}>Duration (e.g., 2022 - Present)</label>
                            <input 
                              type="text" 
                              value={exp.duration} 
                              onChange={(e) => {
                                const updated = [...resumeExperience];
                                updated[idx].duration = e.target.value;
                                setResumeExperience(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                        </div>
                        <div className="form-group">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <label className="form-label" style={{ fontSize: '11px', margin: 0 }}>Job Description / Bullets</label>
                            <button 
                              className="btn" 
                              onClick={() => enhanceResumeSection('experience', exp.description, idx)}
                              disabled={aiEnhancingExpIdx === idx}
                              style={{ fontSize: '10px', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '3px' }}
                            >
                              {aiEnhancingExpIdx === idx ? '✨ Improving...' : '✨ AI Polish Bullets'}
                            </button>
                          </div>
                          <textarea 
                            value={exp.description} 
                            onChange={(e) => {
                              const updated = [...resumeExperience];
                              updated[idx].description = e.target.value;
                              setResumeExperience(updated);
                            }}
                            placeholder="Start each bullet point with '• '"
                            style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '12px', width: '100%', minHeight: '80px', fontSize: '13px', lineHeight: '1.4' }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Accordion 4: Projects */}
                <div className="card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                    <h3 style={{ fontSize: '15px', color: '#fff', margin: 0 }}>
                      🛠️ Personal Projects
                    </h3>
                    <button 
                      className="btn"
                      onClick={() => setResumeProjects([...resumeProjects, { name: '', tech: '', description: '' }])}
                      style={{ fontSize: '11px', padding: '4px 10px' }}
                    >
                      ➕ Add Project
                    </button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {resumeProjects.map((proj, idx) => (
                      <div key={idx} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '16px', position: 'relative' }}>
                        <button 
                          onClick={() => setResumeProjects(resumeProjects.filter((_, i) => i !== idx))}
                          style={{ position: 'absolute', top: '10px', right: '10px', border: 'none', background: 'none', color: '#EF4444', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px' }}
                          title="Remove Entry"
                        >
                          ✕
                        </button>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                          <div className="form-group">
                            <label className="form-label" style={{ fontSize: '11px' }}>Project Name</label>
                            <input 
                              type="text" 
                              value={proj.name} 
                              onChange={(e) => {
                                const updated = [...resumeProjects];
                                updated[idx].name = e.target.value;
                                setResumeProjects(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                          <div className="form-group">
                            <label className="form-label" style={{ fontSize: '11px' }}>Tech Stack Used (e.g. React, Node)</label>
                            <input 
                              type="text" 
                              value={proj.tech} 
                              onChange={(e) => {
                                const updated = [...resumeProjects];
                                updated[idx].tech = e.target.value;
                                setResumeProjects(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                        </div>
                        <div className="form-group">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <label className="form-label" style={{ fontSize: '11px', margin: 0 }}>Project Details / Bullets</label>
                            <button 
                              className="btn" 
                              onClick={() => enhanceResumeSection('project', proj.description, idx)}
                              disabled={aiEnhancingProjIdx === idx}
                              style={{ fontSize: '10px', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: '3px' }}
                            >
                              {aiEnhancingProjIdx === idx ? '✨ Improving...' : '✨ AI Polish Bullets'}
                            </button>
                          </div>
                          <textarea 
                            value={proj.description} 
                            onChange={(e) => {
                              const updated = [...resumeProjects];
                              updated[idx].description = e.target.value;
                              setResumeProjects(updated);
                            }}
                            placeholder="Start each bullet point with '• '"
                            style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '12px', width: '100%', minHeight: '80px', fontSize: '13px', lineHeight: '1.4' }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Accordion 5: Skills */}
                <div className="card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                    <h3 style={{ fontSize: '15px', color: '#fff', margin: 0 }}>
                      💡 Skills & Keywords
                    </h3>
                    <button 
                      className="btn" 
                      onClick={() => enhanceResumeSection('skills', resumeSkills)}
                      disabled={aiSuggestingSkills}
                      style={{ fontSize: '11px', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      {aiSuggestingSkills ? '✨ Analyzing...' : '✨ AI Suggest Skills'}
                    </button>
                  </div>
                  <input 
                    type="text" 
                    value={resumeSkills} 
                    onChange={(e) => setResumeSkills(e.target.value)}
                    placeholder="Java, React, SQL (comma-separated)"
                    style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '6px', padding: '10px 12px', width: '100%', fontSize: '13px' }}
                  />
                  <span style={{ fontSize: '11px', color: '#64748B', marginTop: '6px', display: 'block' }}>Type your skills separated by commas. Our templates will lay them out in standard tags.</span>
                </div>

                {/* Accordion 6: Education */}
                <div className="card" style={{ padding: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '8px' }}>
                    <h3 style={{ fontSize: '15px', color: '#fff', margin: 0 }}>
                      🎓 Education
                    </h3>
                    <button 
                      className="btn"
                      onClick={() => setResumeEducation([...resumeEducation, { school: '', degree: '', duration: '' }])}
                      style={{ fontSize: '11px', padding: '4px 10px' }}
                    >
                      ➕ Add Education
                    </button>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {resumeEducation.map((edu, idx) => (
                      <div key={idx} style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', padding: '16px', position: 'relative' }}>
                        <button 
                          onClick={() => setResumeEducation(resumeEducation.filter((_, i) => i !== idx))}
                          style={{ position: 'absolute', top: '10px', right: '10px', border: 'none', background: 'none', color: '#EF4444', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px' }}
                          title="Remove Entry"
                        >
                          ✕
                        </button>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                          <div className="form-group">
                            <label className="form-label" style={{ fontSize: '11px' }}>School / University</label>
                            <input 
                              type="text" 
                              value={edu.school} 
                              onChange={(e) => {
                                const updated = [...resumeEducation];
                                updated[idx].school = e.target.value;
                                setResumeEducation(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                          <div className="form-group">
                            <label className="form-label" style={{ fontSize: '11px' }}>Degree & Major</label>
                            <input 
                              type="text" 
                              value={edu.degree} 
                              onChange={(e) => {
                                const updated = [...resumeEducation];
                                updated[idx].degree = e.target.value;
                                setResumeEducation(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                          <div className="form-group" style={{ gridColumn: 'span 2' }}>
                            <label className="form-label" style={{ fontSize: '11px' }}>Duration / Graduation Date</label>
                            <input 
                              type="text" 
                              value={edu.duration} 
                              onChange={(e) => {
                                const updated = [...resumeEducation];
                                updated[idx].duration = e.target.value;
                                setResumeEducation(updated);
                              }}
                              style={{ background: 'rgba(11, 16, 32, 0.4)', color: '#fff', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '8px 12px', width: '100%', fontSize: '13px' }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right Column: Preview Pane */}
              <div className="builder-preview-pane">
                {/* Configuration Bar */}
                <div className="preview-controls">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, minWidth: '130px' }}>
                    <label style={{ fontSize: '10px', color: '#B8C1D9', fontWeight: 'bold', textTransform: 'uppercase' }}>Select Template</label>
                    <select 
                      value={resumeTemplate} 
                      onChange={(e) => setResumeTemplate(e.target.value)}
                      style={{ background: 'rgba(11,16,32,0.6)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px', fontSize: '12px', cursor: 'pointer' }}
                    >
                      <option value="modern">Modern Tech</option>
                      <option value="slate">Slate Minimalist</option>
                      <option value="creative">Creative Executive</option>
                      <option value="classic">Academic Classic</option>
                    </select>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, minWidth: '120px' }}>
                    <label style={{ fontSize: '10px', color: '#B8C1D9', fontWeight: 'bold', textTransform: 'uppercase' }}>Accent Color</label>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center', height: '32px' }}>
                      {['#4F8CFF', '#10B981', '#6366F1', '#F59E0B', '#EF4444'].map(color => (
                        <button 
                          key={color}
                          onClick={() => setResumeAccentColor(color)}
                          style={{ width: '20px', height: '20px', borderRadius: '50%', background: color, border: resumeAccentColor === color ? '2px solid #fff' : 'none', cursor: 'pointer', padding: 0 }}
                        />
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, minWidth: '110px' }}>
                    <label style={{ fontSize: '10px', color: '#B8C1D9', fontWeight: 'bold', textTransform: 'uppercase' }}>Font Family</label>
                    <select 
                      value={resumeFontFamily} 
                      onChange={(e) => setResumeFontFamily(e.target.value)}
                      style={{ background: 'rgba(11,16,32,0.6)', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '8px', fontSize: '12px', cursor: 'pointer' }}
                    >
                      <option value="sans-serif">Sans-Serif</option>
                      <option value="serif">Serif (Classic)</option>
                      <option value="monospace">Monospace</option>
                    </select>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 0.5, minWidth: '70px' }}>
                    <label style={{ fontSize: '10px', color: '#B8C1D9', fontWeight: 'bold', textTransform: 'uppercase' }}>Font Size</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input 
                        type="range" 
                        min="11" 
                        max="16" 
                        value={resumeFontSize}
                        onChange={(e) => setResumeFontSize(parseInt(e.target.value))}
                        style={{ width: '60px', accentColor: 'var(--primary)', cursor: 'pointer' }}
                      />
                      <span style={{ fontSize: '11px', color: '#B8C1D9' }}>{resumeFontSize}px</span>
                    </div>
                  </div>
                </div>

                {/* Printable Resume Mockup Page */}
                <div 
                  className="resume-paper"
                  style={{ 
                    fontFamily: resumeFontFamily === 'serif' ? 'Georgia, "Times New Roman", serif' : resumeFontFamily === 'monospace' ? 'Consolas, Monaco, monospace' : '"Inter", sans-serif',
                    fontSize: `${resumeFontSize}px`,
                    lineHeight: 1.4
                  }}
                >
                  {/* Template 1: Modern Tech */}
                  {resumeTemplate === 'modern' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {/* Accent Header Bar */}
                      <div style={{ borderLeft: `6px solid ${resumeAccentColor}`, paddingLeft: '16px', marginBottom: '8px' }}>
                        <h1 style={{ fontSize: '28px', fontWeight: '800', margin: '0 0 4px 0', textTransform: 'uppercase', tracking: '1px', color: '#0f172a' }}>{resumePersonalInfo.name || 'Your Name'}</h1>
                        <h2 style={{ fontSize: '16px', fontWeight: '600', color: resumeAccentColor, margin: 0 }}>{resumePersonalInfo.title || 'Professional Title'}</h2>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '11px', marginTop: '8px', color: '#475569' }}>
                          {resumePersonalInfo.email && <span>📧 {resumePersonalInfo.email}</span>}
                          {resumePersonalInfo.phone && <span>📞 {resumePersonalInfo.phone}</span>}
                          {resumePersonalInfo.website && <span>🌐 {resumePersonalInfo.website}</span>}
                          {resumePersonalInfo.linkedin && <span>🔗 {resumePersonalInfo.linkedin}</span>}
                          {resumePersonalInfo.github && <span>💻 {resumePersonalInfo.github}</span>}
                        </div>
                      </div>

                      {/* Summary */}
                      {resumeSummary && (
                        <div>
                          <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#0f172a', borderBottom: `2px solid ${resumeAccentColor}`, paddingBottom: '3px', marginBottom: '8px' }}>Summary</h3>
                          <p style={{ margin: 0, color: '#334155', textAlign: 'justify' }}>{resumeSummary}</p>
                        </div>
                      )}

                      {/* Experience */}
                      {resumeExperience.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#0f172a', borderBottom: `2px solid ${resumeAccentColor}`, paddingBottom: '3px', marginBottom: '8px' }}>Work Experience</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {resumeExperience.map((exp, idx) => (
                              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontWeight: '700' }}>
                                  <span style={{ fontSize: '13.5px', color: '#0f172a' }}>{exp.role} <span style={{ fontWeight: 'normal', color: '#64748B' }}>at</span> {exp.company}</span>
                                  <span style={{ fontSize: '11px', color: '#64748B' }}>{exp.duration}</span>
                                </div>
                                <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#334155', paddingLeft: '8px' }}>{exp.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Projects */}
                      {resumeProjects.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#0f172a', borderBottom: `2px solid ${resumeAccentColor}`, paddingBottom: '3px', marginBottom: '8px' }}>Projects</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {resumeProjects.map((proj, idx) => (
                              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontWeight: '700' }}>
                                  <span style={{ fontSize: '13.5px', color: '#0f172a' }}>{proj.name}</span>
                                  <span style={{ fontSize: '11px', fontStyle: 'italic', fontWeight: 'normal', color: resumeAccentColor }}>{proj.tech}</span>
                                </div>
                                <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#334155', paddingLeft: '8px' }}>{proj.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Skills */}
                      {resumeSkills && (
                        <div>
                          <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#0f172a', borderBottom: `2px solid ${resumeAccentColor}`, paddingBottom: '3px', marginBottom: '8px' }}>Technical Skills</h3>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                            {resumeSkills.split(',').map(s => s.trim()).filter(Boolean).map((skill, sIdx) => (
                              <span key={sIdx} style={{ fontSize: '11px', background: 'rgba(79, 140, 255, 0.08)', border: `1px solid rgba(79, 140, 255, 0.2)`, padding: '3px 8px', borderRadius: '4px', color: '#0f172a', fontWeight: '500' }}>
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Education */}
                      {resumeEducation.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#0f172a', borderBottom: `2px solid ${resumeAccentColor}`, paddingBottom: '3px', marginBottom: '8px' }}>Education</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {resumeEducation.map((edu, idx) => (
                              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                <span style={{ fontWeight: '700', color: '#0f172a' }}>{edu.degree} <span style={{ fontWeight: 'normal', color: '#64748B' }}>—</span> {edu.school}</span>
                                <span style={{ fontSize: '11px', color: '#64748B', fontWeight: '700' }}>{edu.duration}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Template 2: Slate Minimalist */}
                  {resumeTemplate === 'slate' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
                      {/* Center Header block */}
                      <div style={{ textAlign: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
                        <h1 style={{ fontSize: '26px', fontWeight: '700', margin: '0 0 6px 0', color: '#1e293b' }}>{resumePersonalInfo.name || 'Your Name'}</h1>
                        <h2 style={{ fontSize: '15px', fontWeight: '500', color: '#475569', textTransform: 'uppercase', letterSpacing: '1px', margin: '0 0 10px 0' }}>{resumePersonalInfo.title || 'Professional Title'}</h2>
                        <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '12px', fontSize: '11px', color: '#64748B' }}>
                          {resumePersonalInfo.email && <span>{resumePersonalInfo.email}</span>}
                          {resumePersonalInfo.phone && <span>• {resumePersonalInfo.phone}</span>}
                          {resumePersonalInfo.website && <span>• {resumePersonalInfo.website}</span>}
                          {resumePersonalInfo.linkedin && <span>• {resumePersonalInfo.linkedin}</span>}
                          {resumePersonalInfo.github && <span>• {resumePersonalInfo.github}</span>}
                        </div>
                      </div>

                      {/* Summary */}
                      {resumeSummary && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#475569', letterSpacing: '1px', marginBottom: '8px' }}>Professional Summary</h3>
                          <p style={{ margin: 0, color: '#334155', textAlign: 'justify', lineHeight: '1.5' }}>{resumeSummary}</p>
                        </div>
                      )}

                      {/* Experience */}
                      {resumeExperience.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#475569', letterSpacing: '1px', marginBottom: '8px' }}>Experience</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                            {resumeExperience.map((exp, idx) => (
                              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '600' }}>
                                  <span style={{ color: '#1e293b' }}>{exp.role} — <span style={{ fontWeight: 'normal', color: '#64748B' }}>{exp.company}</span></span>
                                  <span style={{ fontSize: '11px', color: '#64748B' }}>{exp.duration}</span>
                                </div>
                                <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#334155' }}>{exp.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Projects */}
                      {resumeProjects.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#475569', letterSpacing: '1px', marginBottom: '8px' }}>Selected Projects</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {resumeProjects.map((proj, idx) => (
                              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '600' }}>
                                  <span style={{ color: '#1e293b' }}>{proj.name}</span>
                                  <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 'normal' }}>{proj.tech}</span>
                                </div>
                                <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#334155' }}>{proj.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Skills */}
                      {resumeSkills && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#475569', letterSpacing: '1px', marginBottom: '8px' }}>Skills</h3>
                          <p style={{ margin: 0, color: '#334155' }}><strong>Technical Stack:</strong> {resumeSkills}</p>
                        </div>
                      )}

                      {/* Education */}
                      {resumeEducation.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#475569', letterSpacing: '1px', marginBottom: '8px' }}>Education</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {resumeEducation.map((edu, idx) => (
                              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ fontWeight: '600', color: '#1e293b' }}>{edu.degree} — <span style={{ fontWeight: 'normal', color: '#64748B' }}>{edu.school}</span></span>
                                <span style={{ fontSize: '11px', color: '#64748B' }}>{edu.duration}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Template 3: Creative Executive */}
                  {resumeTemplate === 'creative' && (
                    <div style={{ display: 'flex', gap: '24px' }}>
                      {/* Left Column (35%) */}
                      <div style={{ width: '35%', display: 'flex', flexDirection: 'column', gap: '20px', borderRight: '1px solid #e2e8f0', paddingRight: '20px' }}>
                        <div>
                          <h1 style={{ fontSize: '24px', fontWeight: '800', margin: '0 0 4px 0', color: '#1e293b', lineHeight: 1.1 }}>{resumePersonalInfo.name}</h1>
                          <h2 style={{ fontSize: '13px', fontWeight: '600', color: resumeAccentColor, margin: 0 }}>{resumePersonalInfo.title}</h2>
                        </div>

                        {/* Contact details */}
                        <div>
                          <h3 style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', color: '#64748B', letterSpacing: '0.5px', marginBottom: '8px' }}>Contact</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11px', color: '#334155' }}>
                            {resumePersonalInfo.email && <div>📧 {resumePersonalInfo.email}</div>}
                            {resumePersonalInfo.phone && <div>📞 {resumePersonalInfo.phone}</div>}
                            {resumePersonalInfo.website && <div>🌐 {resumePersonalInfo.website.replace(/^https?:\/\//, '')}</div>}
                            {resumePersonalInfo.linkedin && <div>🔗 {resumePersonalInfo.linkedin}</div>}
                            {resumePersonalInfo.github && <div>💻 {resumePersonalInfo.github}</div>}
                          </div>
                        </div>

                        {/* Skills */}
                        {resumeSkills && (
                          <div>
                            <h3 style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', color: '#64748B', letterSpacing: '0.5px', marginBottom: '8px' }}>Expertise</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '11.5px', color: '#334155' }}>
                              {resumeSkills.split(',').map(s => s.trim()).filter(Boolean).map((skill, sIdx) => (
                                <div key={sIdx} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                  <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: resumeAccentColor }} />
                                  <span>{skill}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Education */}
                        {resumeEducation.length > 0 && (
                          <div>
                            <h3 style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', color: '#64748B', letterSpacing: '0.5px', marginBottom: '8px' }}>Education</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                              {resumeEducation.map((edu, idx) => (
                                <div key={idx} style={{ fontSize: '11px', color: '#334155' }}>
                                  <div style={{ fontWeight: '700' }}>{edu.degree}</div>
                                  <div style={{ color: '#64748B' }}>{edu.school}</div>
                                  <div style={{ fontSize: '10px', color: '#94A3B8' }}>{edu.duration}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Right Column (65%) */}
                      <div style={{ width: '65%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {/* Summary */}
                        {resumeSummary && (
                          <div>
                            <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: resumeAccentColor, letterSpacing: '0.5px', marginBottom: '6px' }}>Profile</h3>
                            <p style={{ margin: 0, color: '#334155', textAlign: 'justify' }}>{resumeSummary}</p>
                          </div>
                        )}

                        {/* Experience */}
                        {resumeExperience.length > 0 && (
                          <div>
                            <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: resumeAccentColor, letterSpacing: '0.5px', marginBottom: '10px' }}>Professional Path</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                              {resumeExperience.map((exp, idx) => (
                                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                    <span style={{ fontWeight: '700', color: '#1e293b' }}>{exp.role}</span>
                                    <span style={{ fontSize: '10px', color: '#64748B', fontWeight: '600' }}>{exp.duration}</span>
                                  </div>
                                  <div style={{ fontSize: '11.5px', fontStyle: 'italic', color: '#64748B', marginBottom: '2px' }}>{exp.company}</div>
                                  <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#334155' }}>{exp.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Projects */}
                        {resumeProjects.length > 0 && (
                          <div>
                            <h3 style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: resumeAccentColor, letterSpacing: '0.5px', marginBottom: '10px' }}>Projects</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              {resumeProjects.map((proj, idx) => (
                                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                    <span style={{ fontWeight: '700', color: '#1e293b' }}>{proj.name}</span>
                                    <span style={{ fontSize: '10px', color: resumeAccentColor, fontWeight: '500' }}>{proj.tech}</span>
                                  </div>
                                  <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#334155' }}>{proj.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Template 4: Academic Classic (Serif) */}
                  {resumeTemplate === 'classic' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {/* Fully centered header */}
                      <div style={{ textAlign: 'center' }}>
                        <h1 style={{ fontSize: '24px', fontWeight: 'normal', margin: '0 0 4px 0', fontFamily: 'Georgia, serif', color: '#000' }}>{resumePersonalInfo.name || 'Your Name'}</h1>
                        <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '8px', fontSize: '11px', color: '#000' }}>
                          {resumePersonalInfo.email && <span>{resumePersonalInfo.email}</span>}
                          {resumePersonalInfo.phone && <span>| {resumePersonalInfo.phone}</span>}
                          {resumePersonalInfo.website && <span>| {resumePersonalInfo.website}</span>}
                          {resumePersonalInfo.linkedin && <span>| {resumePersonalInfo.linkedin}</span>}
                          {resumePersonalInfo.github && <span>| {resumePersonalInfo.github}</span>}
                        </div>
                      </div>

                      {/* Summary */}
                      {resumeSummary && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '1px solid #000', paddingBottom: '2px', marginBottom: '6px', color: '#000', textAlign: 'left' }}>Objective</h3>
                          <p style={{ margin: 0, color: '#000', textAlign: 'justify' }}>{resumeSummary}</p>
                        </div>
                      )}

                      {/* Education */}
                      {resumeEducation.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '1px solid #000', paddingBottom: '2px', marginBottom: '6px', color: '#000', textAlign: 'left' }}>Education</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {resumeEducation.map((edu, idx) => (
                              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                <span style={{ color: '#000' }}><strong>{edu.school}</strong> — {edu.degree}</span>
                                <span style={{ fontSize: '11px', color: '#000', fontStyle: 'italic' }}>{edu.duration}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Experience */}
                      {resumeExperience.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '1px solid #000', paddingBottom: '2px', marginBottom: '6px', color: '#000', textAlign: 'left' }}>Professional Experience</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {resumeExperience.map((exp, idx) => (
                              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                  <span style={{ color: '#000' }}><strong>{exp.company}</strong> — {exp.role}</span>
                                  <span style={{ fontSize: '11px', color: '#000', fontStyle: 'italic' }}>{exp.duration}</span>
                                </div>
                                <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#000', paddingLeft: '8px' }}>{exp.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Projects */}
                      {resumeProjects.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '1px solid #000', paddingBottom: '2px', marginBottom: '6px', color: '#000', textAlign: 'left' }}>Selected Projects</h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {resumeProjects.map((proj, idx) => (
                              <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                  <span style={{ color: '#000' }}><strong>{proj.name}</strong> <span style={{ fontWeight: 'normal', fontSize: '11px' }}>({proj.tech})</span></span>
                                </div>
                                <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#000', paddingLeft: '8px' }}>{proj.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Skills */}
                      {resumeSkills && (
                        <div>
                          <h3 style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', borderBottom: '1px solid #000', paddingBottom: '2px', marginBottom: '6px', color: '#000', textAlign: 'left' }}>Skills & Keywords</h3>
                          <p style={{ margin: 0, color: '#000' }}>{resumeSkills}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}


        {/* PAGE 6: HISTORY */}
        {activePage === 'history' && (
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.3 }}
          >
            <div className="page-header">
              <h1 className="page-title">{t('historyTitle')}</h1>
              <p className="page-subtitle">{t('historySubtitle')}</p>
            </div>

            <div className="search-filter-container">
              <div className="search-input-wrapper">
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="🔍 Search resumes by name..." 
                  value={historySearchQuery}
                  onChange={(e) => setHistorySearchQuery(e.target.value)}
                  style={{ width: '100%', paddingLeft: '36px' }}
                />
              </div>

              <div className="filter-sort-wrapper">
                <select 
                  className="dropdown-select" 
                  value={historyFilter}
                  onChange={(e) => setHistoryFilter(e.target.value)}
                >
                  <option value="all">All Scores</option>
                  <option value="strong">Outstanding (76%+)</option>
                  <option value="moderate">Competitive/Adequate (50-75%)</option>
                  <option value="needs_work">Needs Work (&lt;50%)</option>
                </select>

                <select 
                  className="dropdown-select" 
                  value={historySort}
                  onChange={(e) => setHistorySort(e.target.value)}
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="score_desc">Highest Score</option>
                  <option value="score_asc">Lowest Score</option>
                </select>
              </div>
            </div>

            <div className="history-table-container">
              {historyList.length > 0 ? (() => {
                const filteredList = historyList
                  .filter(item => {
                    const matchesSearch = item.fileName.toLowerCase().includes(historySearchQuery.toLowerCase());
                    const score = item.atsScore;
                    let matchesFilter = true;
                    if (historyFilter === 'strong') matchesFilter = score >= 76;
                    else if (historyFilter === 'moderate') matchesFilter = score >= 50 && score < 76;
                    else if (historyFilter === 'needs_work') matchesFilter = score < 50;
                    return matchesSearch && matchesFilter;
                  })
                  .sort((a, b) => {
                    if (historySort === 'newest') return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
                    if (historySort === 'oldest') return new Date(a.createdAt || 0) - new Date(b.createdAt || 0);
                    if (historySort === 'score_desc') return b.atsScore - a.atsScore;
                    if (historySort === 'score_asc') return a.atsScore - b.atsScore;
                    return 0;
                  });

                if (filteredList.length === 0) {
                  return (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#64748B' }}>
                      No history items match your search filters.
                    </div>
                  );
                }

                return (
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Resume Name</th>
                        <th>ATS Score</th>
                        <th>Date Analyzed</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredList.map((item) => {
                        const strength = getResumeStrength(item.atsScore);
                        return (
                          <tr key={item.id}>
                            <td style={{ fontWeight: '600', color: '#fff' }}>📄 {item.fileName}</td>
                            <td>
                              <span className={getScoreColors(item.atsScore).textClass} style={{ fontWeight: '700', fontSize: '14px' }}>
                                {item.atsScore}%
                              </span>
                            </td>
                            <td style={{ color: '#B8C1D9' }}>
                              {item.createdAt ? new Date(item.createdAt).toLocaleString() : 'N/A'}
                            </td>
                            <td>
                              <span className={`badge-neon ${strength.class}`} style={{ fontSize: '9px' }}>
                                {strength.label}
                              </span>
                            </td>
                            <td>
                              <button 
                                className="btn btn-outline" 
                                style={{ padding: '6px 12px', fontSize: '11px', borderRadius: '6px' }}
                                onClick={() => handleLoadHistoryItem(item)}
                              >
                                View Report →
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                );
              })() : (
                <div style={{ padding: '40px', textAlign: 'center', color: '#64748B' }}>
                  {t('noAnalyses')}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* PAGE 7: ABOUT & SUPPORT */}
        {activePage === 'about' && (
          <div>
            <div className="page-header">
              <h1 className="page-title">{t('aboutSupportTitle')}</h1>
              <p className="page-subtitle">{t('aboutSupportSubtitle')}</p>
            </div>

            <div className="about-layout">
              {/* Left Column: About & Developer Profile */}
              <div>
                <div className="card" style={{ marginBottom: '24px' }}>
                  <h3 style={{ fontSize: '16px', marginBottom: '12px', color: '#06B6D4' }}>{t('aboutProjectHeading')}</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                    <div><strong>{t('projectVersion')}:</strong> 1.2.0</div>
                    <div>
                      <strong>{t('techUsed')}:</strong>
                      <div className="tech-tag-container">
                        <span className="tech-tag">React 18</span>
                        <span className="tech-tag">Vite</span>
                        <span className="tech-tag">CSS-in-JS</span>
                        <span className="tech-tag">Spring Boot 3</span>
                        <span className="tech-tag">FastAPI</span>
                        <span className="tech-tag">H2 Database</span>
                        <span className="tech-tag">spaCy</span>
                        <span className="tech-tag">TfidfVectorizer</span>
                        <span className="tech-tag">Cosine Similarity</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="dev-profile-card">
                  <div className="dev-header">
                    <div className="dev-avatar-large">R</div>
                    <div className="dev-meta">
                      <span className="dev-title-name">REJIN</span>
                      <span className="dev-subtitle-role">AI/ML Engineer</span>
                    </div>
                  </div>
                  <div className="dev-details-list">
                    <div className="dev-detail-item">
                      <span>📧</span> 
                      <span><strong>{t('devEmail')}:</strong> <a href="mailto:rrejinrejin123@gmail.com">rrejinrejin123@gmail.com</a></span>
                    </div>
                    <div className="dev-detail-item">
                      <span>🐙</span>
                      <span><strong>{t('devGithub')}:</strong> <a href="https://github.com/rrejinrejinr" target="_blank" rel="noreferrer">github.com/rrejinrejinr</a></span>
                    </div>
                    <div className="dev-detail-item">
                      <span>🔗</span>
                      <span><strong>{t('devLinkedin')}:</strong> <a href="https://www.linkedin.com/in/rejin-r-5b3728352" target="_blank" rel="noreferrer">linkedin.com/rejin-r-5b3728352</a></span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Help & Support Form */}
              <div>
                <div className="support-form-card">
                  {!supportSubmitted ? (
                    <form onSubmit={handleSupportFormSubmit} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <h3 style={{ fontSize: '16px', marginBottom: '10px', color: '#06B6D4' }}>{t('contactSupportHeading')}</h3>
                      <p style={{ fontSize: '12px', color: '#64748B', marginBottom: '20px' }}>{t('supportDesc')}</p>
                      
                      <div className="form-group">
                        <label className="form-label">{t('formNameLabel')}</label>
                        <input 
                          type="text" 
                          className="input-field" 
                          value={supportName} 
                          onChange={(e) => setSupportName(e.target.value)}
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label">{t('formEmailLabel')}</label>
                        <input 
                          type="email" 
                          className="input-field" 
                          value={supportEmail} 
                          onChange={(e) => setSupportEmail(e.target.value)}
                          required
                        />
                      </div>

                      <div className="form-group" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                        <label className="form-label">{t('formMessageLabel')}</label>
                        <textarea 
                          className="form-textarea" 
                          placeholder={t('formMessagePlaceholder')}
                          value={supportMessage}
                          onChange={(e) => setSupportMessage(e.target.value)}
                          style={{ flexGrow: 1, minHeight: '120px' }}
                          required
                        />
                      </div>

                      <button type="submit" className="btn" style={{ width: '100%', marginTop: '10px' }}>
                        ✉️ {t('submitFormBtn')}
                      </button>
                    </form>
                  ) : (
                    <div className="success-banner">
                      <div className="success-icon">✔️</div>
                      <h3 style={{ marginBottom: '10px' }}>{t('ticketSubmittedTitle')}</h3>
                      <p style={{ fontSize: '13px', color: '#94A3B8', marginBottom: '30px' }}>{t('ticketSubmittedMsg')}</p>
                      <button className="btn btn-outline" onClick={handleResetSupportForm}>
                        👈 {t('backToAppBtn')}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

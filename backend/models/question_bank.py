"""
question_bank.py — Phase 6 Mock Interview Question Bank

Structure:
  ROLE_QUESTION_BANK[role][interview_type][difficulty] = [
      {"question": "...", "ideal_answer": "...", "keywords": [...], "category": "..."}
  ]
  SKILL_QUESTION_BANK[skill_name] = [
      {"question": "...", "ideal_answer": "...", "keywords": [...], "category": "skill"}
  ]
  GENERAL_QUESTION_BANK[interview_type] = [
      {"question": "...", "ideal_answer": "...", "keywords": [...], "category": "general"}
  ]
"""

ROLE_QUESTION_BANK = {

    "Data Science": {
        "Technical": {
            "Easy": [
                {
                    "question": "What is the difference between supervised and unsupervised learning?",
                    "ideal_answer": "Supervised learning uses labeled training data where inputs map to known outputs (e.g., classification, regression). Unsupervised learning finds hidden patterns in unlabeled data (e.g., clustering, dimensionality reduction). Examples: supervised - linear regression, decision trees; unsupervised - K-Means, PCA.",
                    "keywords": ["supervised", "unsupervised", "labeled", "unlabeled", "classification", "regression", "clustering", "pattern"],
                    "category": "concept"
                },
                {
                    "question": "Explain what a confusion matrix is and its key metrics.",
                    "ideal_answer": "A confusion matrix shows counts of true positives, true negatives, false positives, and false negatives for a classifier. Key derived metrics: Accuracy (TP+TN/total), Precision (TP/(TP+FP)), Recall/Sensitivity (TP/(TP+FN)), F1-Score (harmonic mean of precision and recall).",
                    "keywords": ["confusion matrix", "true positive", "false positive", "precision", "recall", "f1", "accuracy", "sensitivity"],
                    "category": "evaluation"
                },
                {
                    "question": "What is the purpose of train/test split and cross-validation?",
                    "ideal_answer": "Train/test split divides data so the model trains on one portion and is evaluated on unseen data to estimate generalization. Cross-validation (e.g., k-fold) further reduces evaluation variance by rotating which fold is the test set. It prevents overfitting assessment and gives more reliable performance estimates.",
                    "keywords": ["train", "test", "cross-validation", "overfitting", "generalization", "k-fold", "evaluation", "split"],
                    "category": "methodology"
                },
            ],
            "Medium": [
                {
                    "question": "Explain the bias-variance tradeoff and how it affects model selection.",
                    "ideal_answer": "Bias is systematic error from wrong assumptions; high bias causes underfitting. Variance is sensitivity to small fluctuations in training data; high variance causes overfitting. A good model balances them. Regularization (L1/L2) reduces variance. Simpler models have higher bias. Complex models have higher variance. The goal is minimizing total error = bias² + variance + irreducible noise.",
                    "keywords": ["bias", "variance", "underfitting", "overfitting", "regularization", "l1", "l2", "tradeoff", "complexity"],
                    "category": "concept"
                },
                {
                    "question": "Describe how gradient descent works and its variants.",
                    "ideal_answer": "Gradient descent minimizes a loss function by iteratively updating parameters in the direction of the negative gradient. Batch gradient descent uses all samples per step. Stochastic gradient descent (SGD) uses one sample. Mini-batch uses small batches. Variants like Adam, RMSprop, and Adagrad use adaptive learning rates. Key hyperparameter: learning rate controls step size.",
                    "keywords": ["gradient descent", "loss function", "learning rate", "stochastic", "mini-batch", "adam", "optimizer", "backpropagation", "convergence"],
                    "category": "algorithm"
                },
                {
                    "question": "What techniques do you use to handle imbalanced datasets?",
                    "ideal_answer": "Techniques include: oversampling minority class (SMOTE), undersampling majority class, class_weight parameter in sklearn, using appropriate metrics (F1, AUC-ROC instead of accuracy), ensemble methods like balanced random forest, and adjusting decision thresholds.",
                    "keywords": ["imbalanced", "smote", "oversampling", "undersampling", "class_weight", "auc", "f1", "threshold", "ensemble"],
                    "category": "preprocessing"
                },
                {
                    "question": "Explain how a Random Forest works and why it tends to outperform single decision trees.",
                    "ideal_answer": "Random Forest builds many decision trees using bootstrap sampling (bagging) and random feature subsets at each split. Final prediction aggregates tree outputs (majority vote for classification, mean for regression). It reduces variance without increasing bias significantly. Trees are decorrelated by random feature selection, reducing overfitting compared to a single deep tree.",
                    "keywords": ["random forest", "decision tree", "bagging", "bootstrap", "ensemble", "variance", "feature importance", "overfitting", "decorrelated"],
                    "category": "algorithm"
                },
            ],
            "Hard": [
                {
                    "question": "Explain how XGBoost works and how it differs from standard gradient boosting.",
                    "ideal_answer": "XGBoost uses gradient boosting with second-order Taylor expansion of the loss, L1/L2 regularization, column and row subsampling, tree pruning via 'max_depth' and 'min_child_weight', and parallel computation on the feature level. It adds explicit regularization terms (gamma, lambda, alpha) not in standard GBM, handles sparse data natively, and approximates split finding for speed.",
                    "keywords": ["xgboost", "gradient boosting", "regularization", "taylor", "tree pruning", "sparse", "subsampling", "leaf weight", "shrinkage"],
                    "category": "algorithm"
                },
                {
                    "question": "How would you design a feature store for a production ML system?",
                    "ideal_answer": "A feature store separates feature computation from model training and serving. It includes an offline store (data warehouse/Hive for batch features), an online store (Redis/DynamoDB for low-latency serving), a feature registry (metadata, lineage, versioning), and a computation layer (Spark, Flink). Key concerns: point-in-time correctness to prevent data leakage, feature reuse across teams, and consistency between training and serving.",
                    "keywords": ["feature store", "offline store", "online store", "point-in-time", "data leakage", "versioning", "serving", "training-serving skew", "registry"],
                    "category": "mlops"
                },
            ],
        },
        "Behavioral": {
            "Easy": [
                {
                    "question": "Describe a data science project you are proud of. What was your contribution?",
                    "ideal_answer": "A strong answer describes the problem context, the candidate's specific role, methods used (data collection, feature engineering, modeling, evaluation), challenges overcome, and measurable outcomes or business impact.",
                    "keywords": ["project", "contribution", "problem", "model", "result", "impact", "team", "challenge", "outcome"],
                    "category": "behavioral"
                },
                {
                    "question": "How do you communicate complex model results to non-technical stakeholders?",
                    "ideal_answer": "Use visual aids (charts, dashboards), avoid jargon, focus on business impact rather than metrics (revenue impact, error reduction), use analogies, provide executive summaries, and tailor depth to the audience. Storytelling with data is key.",
                    "keywords": ["communication", "visualization", "stakeholder", "business impact", "jargon", "summary", "storytelling", "dashboard", "non-technical"],
                    "category": "communication"
                },
            ],
            "Medium": [
                {
                    "question": "Tell me about a time your model failed in production. How did you handle it?",
                    "ideal_answer": "A strong answer covers: detecting the failure (monitoring/alerting), root cause analysis (data drift, concept drift, pipeline bug), immediate mitigation (rollback, fallback), long-term fix (retraining, data quality checks, better monitoring), and lessons learned.",
                    "keywords": ["model failure", "monitoring", "data drift", "rollback", "root cause", "mitigation", "retraining", "production", "alerting"],
                    "category": "behavioral"
                },
            ],
            "Hard": [
                {
                    "question": "How do you approach ethical considerations in machine learning model development?",
                    "ideal_answer": "Address: bias detection and fairness metrics (demographic parity, equal opportunity), explainability (SHAP, LIME), privacy (differential privacy, data anonymization), transparency in model limitations, regulatory compliance (GDPR), human-in-the-loop for high-stakes decisions, and ongoing monitoring for disparate impact.",
                    "keywords": ["bias", "fairness", "explainability", "shap", "privacy", "gdpr", "transparency", "ethical", "disparate impact", "accountability"],
                    "category": "ethics"
                },
            ],
        },
        "HR": {
            "Easy": [
                {
                    "question": "Why do you want to work as a Data Scientist at this company?",
                    "ideal_answer": "Strong answers connect personal skills and passion to the company's mission, reference specific products or data-driven decisions they make, and show genuine research about the company's data culture.",
                    "keywords": ["motivation", "company", "data", "passion", "fit", "mission", "skills", "growth", "interest"],
                    "category": "hr"
                },
                {
                    "question": "Where do you see yourself in 5 years in the data science field?",
                    "ideal_answer": "Candidates should express a realistic growth trajectory — deepening expertise, leading projects, becoming a senior/principal data scientist, or moving into ML engineering or research. Should align with the company's growth opportunities.",
                    "keywords": ["growth", "career", "leadership", "expertise", "senior", "long-term", "learning", "contribution"],
                    "category": "hr"
                },
            ],
            "Medium": [
                {
                    "question": "How do you stay up to date with the latest developments in machine learning and AI?",
                    "ideal_answer": "Following ArXiv, Papers With Code, ML Twitter/LinkedIn, NeurIPS/ICML/ICLR proceedings, reading newsletters (Import AI, The Batch), online courses (fast.ai, Coursera), contributing to open source, attending meetups/conferences, and reproducing papers.",
                    "keywords": ["arxiv", "papers", "conferences", "learning", "course", "blog", "community", "research", "trends"],
                    "category": "hr"
                },
            ],
            "Hard": [],
        },
        "Mixed": {},
    },

    "Java Developer": {
        "Technical": {
            "Easy": [
                {
                    "question": "Explain the difference between an abstract class and an interface in Java.",
                    "ideal_answer": "Abstract classes can have state (fields), constructors, and method implementations; a class can only extend one abstract class. Interfaces define contracts with default/static methods since Java 8, support multiple implementation. Use abstract class for shared base behavior; use interface for type contracts and multiple inheritance of behavior.",
                    "keywords": ["abstract class", "interface", "inheritance", "multiple", "fields", "constructor", "default method", "implements", "extends"],
                    "category": "oop"
                },
                {
                    "question": "What is the difference between == and .equals() in Java?",
                    "ideal_answer": "== compares object references (memory addresses) for objects, and values for primitives. .equals() compares logical/value equality as defined by the class. For String, == may return false for two identical strings if they are different objects, while .equals() returns true. Always use .equals() for content comparison.",
                    "keywords": ["equals", "reference", "value", "string", "comparison", "object", "primitive", "identity", "semantic"],
                    "category": "fundamentals"
                },
                {
                    "question": "Explain Java's memory model: heap, stack, and garbage collection.",
                    "ideal_answer": "The heap stores objects and class instances shared across threads. The stack stores method call frames, local variables, and references — each thread has its own stack. Garbage collection automatically reclaims unreachable heap objects. JVM uses GC algorithms (G1, ZGC, Shenandoah). Developers avoid manual memory management but can influence GC via object lifecycle design.",
                    "keywords": ["heap", "stack", "garbage collection", "memory", "jvm", "thread", "gc", "object", "reference", "generation"],
                    "category": "jvm"
                },
            ],
            "Medium": [
                {
                    "question": "Explain the SOLID principles and give an example of each.",
                    "ideal_answer": "Single Responsibility — one class, one reason to change. Open/Closed — open for extension, closed for modification. Liskov Substitution — subclasses must be substitutable for base classes. Interface Segregation — no client forced to depend on unused methods. Dependency Inversion — depend on abstractions, not concretions. Applied via inheritance, composition, dependency injection.",
                    "keywords": ["solid", "single responsibility", "open closed", "liskov", "interface segregation", "dependency inversion", "abstraction", "composition"],
                    "category": "design"
                },
                {
                    "question": "How does Spring Boot auto-configuration work?",
                    "ideal_answer": "Spring Boot scans @EnableAutoConfiguration, which triggers spring.factories/AutoConfiguration.imports to load conditional configuration classes. @ConditionalOnClass, @ConditionalOnMissingBean, @ConditionalOnProperty control which beans are created based on classpath and properties. This provides opinionated defaults while allowing override.",
                    "keywords": ["spring boot", "auto-configuration", "conditional", "beans", "classpath", "starter", "application context", "spring.factories", "annotation"],
                    "category": "spring"
                },
                {
                    "question": "Explain Java concurrency: synchronized, volatile, and the java.util.concurrent package.",
                    "ideal_answer": "synchronized ensures mutual exclusion and memory visibility for a block/method. volatile guarantees visibility of writes across threads without mutual exclusion. java.util.concurrent provides higher-level abstractions: Executors, thread pools, ConcurrentHashMap, CountDownLatch, Semaphore, CompletableFuture, avoiding low-level lock issues.",
                    "keywords": ["synchronized", "volatile", "concurrent", "thread", "executor", "lock", "atomicity", "visibility", "completablefuture", "thread pool"],
                    "category": "concurrency"
                },
            ],
            "Hard": [
                {
                    "question": "Describe how you would design a high-throughput, low-latency REST API in Java/Spring Boot.",
                    "ideal_answer": "Use Spring WebFlux (reactive, non-blocking I/O), connection pooling (HikariCP), caching layers (Redis, Caffeine), async processing, optimized database queries (indexes, projection queries), response compression, HTTP/2, CDN for static assets, load balancing, circuit breakers (Resilience4j), and horizontal scaling with stateless service design.",
                    "keywords": ["reactive", "non-blocking", "connection pool", "cache", "redis", "async", "index", "circuit breaker", "load balancing", "stateless"],
                    "category": "system design"
                },
            ],
        },
        "Behavioral": {
            "Easy": [
                {
                    "question": "Describe a challenging Java project you worked on and what you learned from it.",
                    "ideal_answer": "Answer should describe the problem, technical complexity, specific Java/Spring technologies used, challenges faced (performance, concurrency, integration), how they were resolved, and key learnings applied later.",
                    "keywords": ["challenge", "project", "java", "spring", "problem", "solution", "learning", "technical", "team", "outcome"],
                    "category": "behavioral"
                },
            ],
            "Medium": [
                {
                    "question": "How do you approach code reviews and ensure code quality in a Java team?",
                    "ideal_answer": "Define coding standards and style guides (Google Java Style, Checkstyle), enforce static analysis (SonarQube, PMD, SpotBugs), use PR review checklists (logic, tests, security, performance), pair programming for complex areas, enforce test coverage thresholds, and foster a collaborative, constructive review culture.",
                    "keywords": ["code review", "quality", "static analysis", "sonarqube", "testing", "coverage", "standards", "checkstyle", "pr", "best practices"],
                    "category": "process"
                },
            ],
            "Hard": [],
        },
        "HR": {
            "Easy": [
                {
                    "question": "Why do you prefer Java as your primary language?",
                    "ideal_answer": "Strong answers cite: JVM ecosystem maturity, enterprise reliability, rich ecosystem (Spring, Maven, Gradle), strong typing for large codebases, extensive library support, backward compatibility, and wide industry adoption.",
                    "keywords": ["java", "jvm", "ecosystem", "enterprise", "spring", "strong typing", "reliability", "community", "library"],
                    "category": "hr"
                },
            ],
            "Medium": [],
            "Hard": [],
        },
        "Mixed": {},
    },

    "Web Designing": {
        "Technical": {
            "Easy": [
                {
                    "question": "Explain the CSS Box Model and how it affects layout.",
                    "ideal_answer": "Every HTML element is a rectangular box with: content, padding (space inside border), border, and margin (space outside border). box-sizing: border-box includes padding/border in width. box-sizing: content-box (default) adds padding/border outside the width. Understanding box model is essential for accurate spacing and layout.",
                    "keywords": ["box model", "padding", "border", "margin", "content", "box-sizing", "layout", "css", "width"],
                    "category": "css"
                },
                {
                    "question": "What is responsive design and how do you implement it?",
                    "ideal_answer": "Responsive design adapts layouts to different screen sizes. Techniques: CSS media queries for breakpoints, flexible grid systems (CSS Grid, Flexbox), relative units (%, em, rem, vw/vh), fluid images (max-width: 100%), mobile-first approach, and frameworks like Bootstrap or Tailwind CSS.",
                    "keywords": ["responsive", "media query", "flexbox", "grid", "mobile-first", "breakpoint", "fluid", "viewport", "tailwind", "bootstrap"],
                    "category": "design"
                },
            ],
            "Medium": [
                {
                    "question": "Explain the difference between Flexbox and CSS Grid and when to use each.",
                    "ideal_answer": "Flexbox is one-dimensional (row or column), ideal for aligning items in a single axis, navigation bars, or form controls. CSS Grid is two-dimensional, ideal for complex page layouts with rows and columns simultaneously. Use Flexbox for component-level layout; use Grid for page-level layout. They can be combined.",
                    "keywords": ["flexbox", "grid", "one-dimensional", "two-dimensional", "layout", "row", "column", "alignment", "css", "responsive"],
                    "category": "css"
                },
            ],
            "Hard": [
                {
                    "question": "How would you optimize a website's performance for Core Web Vitals?",
                    "ideal_answer": "Core Web Vitals: LCP (Largest Contentful Paint) — optimize images, preload critical resources, use CDN. FID/INP (Interaction to Next Paint) — minimize JavaScript, use web workers. CLS (Cumulative Layout Shift) — reserve space for dynamic content, avoid injecting content above existing content. Also: lazy loading, code splitting, font display swap, HTTP/2, compression (Brotli/gzip).",
                    "keywords": ["core web vitals", "lcp", "cls", "fid", "lazy loading", "cdn", "optimization", "image", "code splitting", "performance"],
                    "category": "performance"
                },
            ],
        },
        "Behavioral": {
            "Easy": [
                {
                    "question": "Walk me through your design process for a new web page or UI component.",
                    "ideal_answer": "Define requirements and user needs → wireframing/sketching → visual design in Figma/Photoshop → design review → HTML/CSS implementation → cross-browser testing → user testing/feedback → iteration.",
                    "keywords": ["design process", "wireframe", "figma", "prototype", "user", "iteration", "feedback", "component", "implementation"],
                    "category": "process"
                },
            ],
            "Medium": [],
            "Hard": [],
        },
        "HR": {
            "Easy": [
                {
                    "question": "How do you balance aesthetic design with usability and accessibility?",
                    "ideal_answer": "Great design is both beautiful and functional. Follow WCAG 2.1 for accessibility (color contrast, ARIA labels, keyboard navigation), user-test with diverse users including those with disabilities, use semantic HTML, ensure readability and visual hierarchy, and never sacrifice usability for aesthetics.",
                    "keywords": ["accessibility", "wcag", "usability", "aria", "semantic", "contrast", "keyboard", "user testing", "aesthetic", "balance"],
                    "category": "hr"
                },
            ],
            "Medium": [],
            "Hard": [],
        },
        "Mixed": {},
    },

    "Python Developer": {
        "Technical": {
            "Easy": [
                {
                    "question": "What are Python decorators and how do you use them?",
                    "ideal_answer": "Decorators are functions that wrap another function or class to extend behavior without modification. They use @syntax. Common examples: @staticmethod, @classmethod, @property, @functools.wraps, @app.route in Flask. They implement the decorator design pattern, enabling concerns like logging, authentication, and caching to be added cleanly.",
                    "keywords": ["decorator", "wrapper", "function", "syntax", "@", "functools", "pattern", "behavior", "closure", "higher-order"],
                    "category": "python"
                },
                {
                    "question": "Explain Python's GIL and its impact on multi-threading.",
                    "ideal_answer": "The Global Interpreter Lock (GIL) is a mutex in CPython that allows only one thread to execute Python bytecode at a time. This means CPU-bound tasks don't benefit from threading in CPython. Solutions: use multiprocessing for CPU-bound work (each process has its own GIL), use async/await for I/O-bound work, or use C extensions that release the GIL (NumPy, PyTorch).",
                    "keywords": ["gil", "global interpreter lock", "threading", "multiprocessing", "cpu-bound", "io-bound", "cpython", "async", "await", "concurrency"],
                    "category": "python"
                },
            ],
            "Medium": [
                {
                    "question": "Explain Python's asyncio and when to use it over threading or multiprocessing.",
                    "ideal_answer": "asyncio provides cooperative multitasking using an event loop. async/await enables non-blocking I/O without threads. Best for high-concurrency I/O-bound tasks (HTTP clients, WebSockets, database queries with async drivers). Unlike threads (OS-managed, shared memory, GIL-limited) and processes (separate memory, high overhead), asyncio has low overhead and no GIL issue, but won't speed up CPU-bound tasks.",
                    "keywords": ["asyncio", "async", "await", "event loop", "coroutine", "non-blocking", "io-bound", "thread", "process", "concurrency"],
                    "category": "python"
                },
            ],
            "Hard": [
                {
                    "question": "How would you design a scalable Python microservice with FastAPI for high traffic?",
                    "ideal_answer": "Use async endpoint handlers in FastAPI, async database drivers (asyncpg, databases), connection pooling, Pydantic for validation, dependency injection for shared resources, middleware for auth and logging, Uvicorn + Gunicorn for serving, Redis for caching and rate limiting, structured logging, distributed tracing, and horizontal scaling behind a load balancer.",
                    "keywords": ["fastapi", "async", "uvicorn", "pydantic", "connection pool", "redis", "middleware", "dependency injection", "scaling", "microservice"],
                    "category": "architecture"
                },
            ],
        },
        "Behavioral": {
            "Easy": [
                {
                    "question": "Describe a complex Python project you built. What design patterns did you apply?",
                    "ideal_answer": "Answer should include project context, specific Python libraries, design patterns applied (MVC, Repository, Singleton, Factory, Observer), challenges addressed, and measurable outcomes.",
                    "keywords": ["project", "design pattern", "python", "library", "architecture", "challenge", "solution", "outcome", "team"],
                    "category": "behavioral"
                },
            ],
            "Medium": [],
            "Hard": [],
        },
        "HR": {
            "Easy": [
                {
                    "question": "Why do you prefer Python and what are its main limitations?",
                    "ideal_answer": "Python's strengths: readability, rich ecosystem (NumPy, Pandas, Django, FastAPI), rapid prototyping, versatility across domains. Limitations: GIL limits CPU-bound parallelism, slower execution than compiled languages, dynamic typing can cause runtime errors, memory overhead. Mitigations: Cython, C extensions, type hints, mypy.",
                    "keywords": ["python", "readability", "ecosystem", "gil", "dynamic typing", "performance", "limitations", "type hints", "prototyping"],
                    "category": "hr"
                },
            ],
            "Medium": [],
            "Hard": [],
        },
        "Mixed": {},
    },

    "DevOps Engineer": {
        "Technical": {
            "Easy": [
                {
                    "question": "Explain the difference between Docker containers and virtual machines.",
                    "ideal_answer": "VMs virtualize hardware and run a full OS per VM via a hypervisor — heavy, slow startup, high resource use. Containers share the host OS kernel, virtualizing only the application layer — lightweight, fast startup, portable. Docker packages code + dependencies into images; containers are running instances. Containers are less isolated than VMs but far more efficient.",
                    "keywords": ["docker", "container", "virtual machine", "hypervisor", "kernel", "image", "isolation", "lightweight", "portability", "os"],
                    "category": "containers"
                },
            ],
            "Medium": [
                {
                    "question": "Describe a CI/CD pipeline you have designed and the tools used.",
                    "ideal_answer": "A typical pipeline: source push → CI trigger (Jenkins/GitHub Actions/GitLab CI) → build (Maven/Gradle/Docker build) → unit tests → static analysis (SonarQube) → security scan → artifact storage (Nexus/ECR) → deploy to staging → integration/smoke tests → deploy to production (blue-green or canary) → monitoring (Prometheus/Grafana).",
                    "keywords": ["ci/cd", "pipeline", "jenkins", "github actions", "docker", "testing", "deployment", "staging", "production", "monitoring"],
                    "category": "cicd"
                },
            ],
            "Hard": [],
        },
        "Behavioral": {
            "Easy": [
                {
                    "question": "Describe a production incident you handled. What was your process?",
                    "ideal_answer": "Detection (alerting/monitoring), escalation, triage (identify blast radius), immediate mitigation (rollback, traffic rerouting), root cause analysis, postmortem/blameless review, corrective actions and monitoring improvements.",
                    "keywords": ["incident", "monitoring", "alert", "rollback", "root cause", "postmortem", "mitigation", "on-call", "escalation"],
                    "category": "behavioral"
                },
            ],
            "Medium": [],
            "Hard": [],
        },
        "HR": {
            "Easy": [],
            "Medium": [],
            "Hard": [],
        },
        "Mixed": {},
    },
}

# Skill-specific questions — mapped from skill names (normalized lowercase)
SKILL_QUESTION_BANK = {
    "python": [
        {
            "question": "How do you manage Python dependencies and virtual environments in a production project?",
            "ideal_answer": "Use venv or virtualenv for isolation, requirements.txt or poetry/pyproject.toml for dependency pinning, pip-compile for deterministic builds, and Docker for reproducible production environments. Separate dev and prod dependencies.",
            "keywords": ["venv", "virtualenv", "requirements", "poetry", "pip", "docker", "dependency", "isolation", "pinning"],
            "category": "skill"
        },
        {
            "question": "Explain Python's context managers and the 'with' statement.",
            "ideal_answer": "Context managers implement __enter__ and __exit__ to manage resources (files, locks, DB connections). The 'with' statement guarantees __exit__ runs even on exceptions. Custom context managers use the contextlib.contextmanager decorator with yield.",
            "keywords": ["context manager", "with", "__enter__", "__exit__", "contextlib", "resource", "exception", "yield", "cleanup"],
            "category": "skill"
        },
    ],
    "machine learning": [
        {
            "question": "Explain the difference between parametric and non-parametric machine learning models.",
            "ideal_answer": "Parametric models assume a fixed functional form with a finite set of parameters (linear regression, logistic regression, neural networks). Non-parametric models make fewer assumptions and grow complexity with data (k-NN, decision trees, Gaussian processes). Parametric models are faster and need less data; non-parametric models are more flexible.",
            "keywords": ["parametric", "non-parametric", "parameters", "linear", "logistic regression", "k-nn", "gaussian", "flexibility", "assumptions"],
            "category": "skill"
        },
    ],
    "deep learning": [
        {
            "question": "Explain vanishing gradients in deep neural networks and how to address them.",
            "ideal_answer": "Vanishing gradients occur when gradients become exponentially small during backpropagation through many layers, especially with sigmoid/tanh activations. Solutions: ReLU activations, batch normalization, residual connections (skip connections / ResNets), gradient clipping, careful weight initialization (He, Xavier).",
            "keywords": ["vanishing gradient", "backpropagation", "relu", "batch normalization", "residual", "skip connection", "resnet", "activation", "initialization"],
            "category": "skill"
        },
    ],
    "tensorflow": [
        {
            "question": "How do you implement and train a neural network in TensorFlow/Keras?",
            "ideal_answer": "Define model architecture using Sequential or Functional API. Compile with optimizer (Adam), loss function (categorical_crossentropy, mse), and metrics. Fit using model.fit() with training data, epochs, batch_size, validation_split. Use callbacks (EarlyStopping, ModelCheckpoint, TensorBoard) for training control.",
            "keywords": ["tensorflow", "keras", "sequential", "compile", "optimizer", "loss", "epoch", "batch", "callback", "model.fit"],
            "category": "skill"
        },
    ],
    "pytorch": [
        {
            "question": "Explain PyTorch's autograd mechanism and how it computes gradients.",
            "ideal_answer": "PyTorch builds a dynamic computation graph (define-by-run). Tensors with requires_grad=True track operations. loss.backward() traverses the graph backward to compute gradients via chain rule. optimizer.step() updates parameters; optimizer.zero_grad() clears gradients before each step.",
            "keywords": ["autograd", "gradient", "backward", "computation graph", "requires_grad", "optimizer", "zero_grad", "dynamic", "chain rule"],
            "category": "skill"
        },
    ],
    "scikit-learn": [
        {
            "question": "Explain sklearn's Pipeline and why it is important for production ML.",
            "ideal_answer": "sklearn Pipeline chains preprocessing steps and estimators into a single object. It prevents data leakage (transforms fit on training data only), enables cross-validation over all steps, simplifies deployment (serialize one object), and ensures consistency between training and inference.",
            "keywords": ["pipeline", "sklearn", "preprocessing", "leakage", "cross-validation", "serialization", "estimator", "fit", "transform", "consistency"],
            "category": "skill"
        },
    ],
    "sql": [
        {
            "question": "Explain the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN.",
            "ideal_answer": "INNER JOIN returns rows matching in both tables. LEFT JOIN returns all rows from the left table and matching rows from the right (NULL for non-matching right rows). FULL OUTER JOIN returns all rows from both tables, with NULLs where there's no match on either side.",
            "keywords": ["inner join", "left join", "outer join", "null", "rows", "tables", "matching", "sql", "database"],
            "category": "skill"
        },
    ],
    "postgresql": [
        {
            "question": "What are PostgreSQL indexes and how do you decide which columns to index?",
            "ideal_answer": "Indexes speed up data retrieval at the cost of write performance and storage. Index columns frequently used in WHERE, JOIN, and ORDER BY clauses with high cardinality. Avoid indexing small tables or columns with low selectivity. Use EXPLAIN ANALYZE to verify index usage. PostgreSQL supports B-tree (default), hash, GIN, GiST, and BRIN indexes.",
            "keywords": ["index", "b-tree", "cardinality", "explain analyze", "where", "join", "performance", "selectivity", "write overhead", "gin"],
            "category": "skill"
        },
    ],
    "fastapi": [
        {
            "question": "Explain dependency injection in FastAPI and give a real use case.",
            "ideal_answer": "FastAPI's Depends() system injects dependencies into route handlers. Common use cases: database session injection (get_db), current user extraction (get_current_user from JWT), shared config objects, or external service clients. Dependencies can be nested and are automatically resolved per-request, making testing easier via dependency overrides.",
            "keywords": ["depends", "dependency injection", "fastapi", "database session", "jwt", "authentication", "testing", "override", "per-request"],
            "category": "skill"
        },
    ],
    "spring boot": [
        {
            "question": "Explain Spring Boot's dependency injection and the difference between @Autowired, @Bean, and @Component.",
            "ideal_answer": "@Component marks a class for Spring to manage as a bean (detected via component scanning). @Bean defines a bean in a @Configuration class, useful for third-party library integration. @Autowired injects dependencies into fields, constructors, or setters. Constructor injection is preferred for testability and immutability.",
            "keywords": ["spring", "autowired", "bean", "component", "injection", "configuration", "constructor injection", "ioc", "container", "scanning"],
            "category": "skill"
        },
    ],
    "docker": [
        {
            "question": "Explain the difference between a Dockerfile's COPY and ADD commands and best practices for writing Dockerfiles.",
            "ideal_answer": "COPY is preferred — it simply copies files from host to image. ADD has extra magic (URL fetching, tar extraction) that makes it harder to reason about. Best practices: use official base images, minimize layers, order instructions by change frequency, use .dockerignore, avoid running as root, use multi-stage builds to reduce final image size, pin image versions.",
            "keywords": ["dockerfile", "copy", "add", "best practice", "layer", "multi-stage", "dockerignore", "base image", "root", "image size"],
            "category": "skill"
        },
    ],
    "aws": [
        {
            "question": "Explain the key differences between EC2, Lambda, and ECS for deploying a Python application.",
            "ideal_answer": "EC2 is a virtual server — full control, persistent, requires OS management. Lambda is serverless — event-driven, no server management, limited execution time (15 min), auto-scales, pay per invocation. ECS is container orchestration — deploys Docker containers on EC2 or Fargate (serverless compute). Choose Lambda for event-driven short tasks, ECS for containerized microservices, EC2 for custom requirements.",
            "keywords": ["ec2", "lambda", "ecs", "serverless", "fargate", "container", "auto-scale", "serverless", "deployment", "managed"],
            "category": "skill"
        },
    ],
    "html": [
        {
            "question": "Explain the purpose of semantic HTML and give examples.",
            "ideal_answer": "Semantic HTML uses elements that convey meaning about the content. Examples: <header>, <nav>, <main>, <article>, <section>, <aside>, <footer>, <figure>, <time>. Benefits: better accessibility (screen readers), improved SEO (search engines understand structure), and cleaner code. Replace generic <div> and <span> with meaningful elements where appropriate.",
            "keywords": ["semantic", "header", "nav", "article", "section", "accessibility", "seo", "screen reader", "meaningful", "html5"],
            "category": "skill"
        },
    ],
    "css": [
        {
            "question": "Explain CSS specificity and how it determines which styles are applied.",
            "ideal_answer": "Specificity determines which CSS rule wins when multiple rules target the same element. Calculated as: inline styles (1000), ID selectors (100), class/attribute/pseudo-class selectors (10), element/pseudo-element selectors (1). Higher specificity wins; equal specificity → last rule wins. !important overrides all but should be avoided.",
            "keywords": ["specificity", "id", "class", "element", "inline", "cascade", "important", "selector", "priority", "css"],
            "category": "skill"
        },
    ],
    "javascript": [
        {
            "question": "Explain JavaScript's event loop and how it handles asynchronous code.",
            "ideal_answer": "JS is single-threaded. The event loop continuously checks the call stack. When async operations complete (timers, HTTP requests), their callbacks are queued in the callback/task queue (or microtask queue for Promises). The event loop processes microtasks (Promises) first, then macrotasks (setTimeout, setInterval). This enables non-blocking I/O without threads.",
            "keywords": ["event loop", "call stack", "async", "callback", "promise", "microtask", "macrotask", "non-blocking", "single-threaded", "settimeout"],
            "category": "skill"
        },
    ],
    "react": [
        {
            "question": "Explain React's virtual DOM and how reconciliation works.",
            "ideal_answer": "React maintains a lightweight virtual DOM (in-memory tree). On state/prop changes, React re-renders the virtual tree and diffs it against the previous version using the reconciliation algorithm (Fiber). Only actual DOM nodes that changed are updated (patch). Keys help React identify list items efficiently. This minimizes expensive real DOM operations.",
            "keywords": ["virtual dom", "reconciliation", "fiber", "diff", "state", "props", "key", "render", "dom", "update"],
            "category": "skill"
        },
    ],
    "java": [
        {
            "question": "Explain Java generics and their benefits for type safety.",
            "ideal_answer": "Generics allow classes and methods to operate on parameterized types (e.g., List<String>). Benefits: compile-time type safety (no ClassCastException at runtime), elimination of casts, and code reuse. Type erasure means generic type info is erased at runtime. Bounded wildcards (<? extends T>, <? super T>) allow flexible, safe use of generic types.",
            "keywords": ["generics", "type safety", "parameterized", "type erasure", "wildcard", "compile time", "cast", "bounded", "list", "collection"],
            "category": "skill"
        },
    ],
    "kubernetes": [
        {
            "question": "Explain the role of a Kubernetes Deployment versus a StatefulSet.",
            "ideal_answer": "Deployment manages stateless pods — any pod is interchangeable, rolling updates, easy scaling. StatefulSet manages stateful applications (databases, message queues) — gives pods stable network identity, stable persistent storage per pod, and ordered deployment/scaling. Use Deployment for web servers/APIs; use StatefulSet for Cassandra, Kafka, PostgreSQL on Kubernetes.",
            "keywords": ["deployment", "statefulset", "stateless", "stateful", "pod", "persistent", "rolling update", "scaling", "identity", "kubernetes"],
            "category": "skill"
        },
    ],
}

# General questions used across all roles
GENERAL_QUESTION_BANK = {
    "Technical": [
        {
            "question": "Explain the concept of RESTful APIs and what makes an API truly RESTful.",
            "ideal_answer": "REST (Representational State Transfer) principles: stateless client-server communication, uniform interface (resources identified by URIs), standard HTTP verbs (GET, POST, PUT, DELETE, PATCH), representation of resources (JSON/XML), hypermedia (HATEOAS optional). RESTful APIs are stateless (no server-side session), use proper HTTP status codes, and have consistent resource naming.",
            "keywords": ["rest", "api", "stateless", "http", "get", "post", "put", "delete", "uri", "json", "status code"],
            "category": "general"
        },
        {
            "question": "What is the difference between SQL and NoSQL databases? When would you choose each?",
            "ideal_answer": "SQL databases use structured schemas, ACID transactions, joins, and are ideal for relational data with complex queries (PostgreSQL, MySQL). NoSQL databases (MongoDB, Redis, Cassandra) sacrifice ACID for flexibility, scale, or speed — document stores for variable schemas, key-value for caching, column-family for time-series, graph DBs for relationships. Choose SQL for structured, relational data; NoSQL for scale, flexibility, or specialized access patterns.",
            "keywords": ["sql", "nosql", "acid", "relational", "schema", "mongodb", "redis", "transaction", "scale", "document"],
            "category": "general"
        },
        {
            "question": "Explain version control best practices with Git in a team environment.",
            "ideal_answer": "Use feature branches (GitFlow or trunk-based development), meaningful commit messages (conventional commits), pull requests with code review, protected main/master branch requiring reviews, rebasing or squashing for clean history, semantic versioning for releases, CI integration on PRs, and .gitignore for build artifacts.",
            "keywords": ["git", "branch", "pull request", "code review", "commit", "merge", "rebase", "gitflow", "ci", "versioning"],
            "category": "general"
        },
    ],
    "Behavioral": [
        {
            "question": "Tell me about a time you had to learn a new technology quickly for a project.",
            "ideal_answer": "Strong answers demonstrate: identifying learning resources quickly (docs, tutorials, courses), building a proof of concept, asking colleagues/community for guidance, time management under pressure, and applying the new skill successfully to the project.",
            "keywords": ["learning", "technology", "self-taught", "documentation", "deadline", "skill", "adapt", "challenge", "research"],
            "category": "general"
        },
        {
            "question": "Describe a situation where you disagreed with a technical decision. How did you handle it?",
            "ideal_answer": "Demonstrate: respectful disagreement, presenting evidence/data to support your view, actively listening to counterarguments, willingness to compromise, following the team decision when appropriate, and escalating through proper channels if necessary.",
            "keywords": ["disagreement", "communication", "evidence", "compromise", "respect", "team", "escalate", "decision", "alternative"],
            "category": "general"
        },
        {
            "question": "Describe a time you had to work with a difficult team member. What was the outcome?",
            "ideal_answer": "Strong answers show emotional intelligence: addressing conflict directly but professionally, seeking to understand the other person's perspective, involving a manager if needed, focusing on work outcomes rather than personalities, and preserving the working relationship.",
            "keywords": ["conflict", "teamwork", "communication", "empathy", "resolution", "professional", "perspective", "outcome", "collaboration"],
            "category": "general"
        },
    ],
    "HR": [
        {
            "question": "What are your greatest technical strengths and an area you are actively improving?",
            "ideal_answer": "Strengths should be specific and relevant (not 'hard-working'). Improvement area should be genuine and show self-awareness with a concrete learning plan.",
            "keywords": ["strength", "improvement", "skill", "learning", "honest", "specific", "plan", "growth", "self-aware"],
            "category": "general"
        },
        {
            "question": "How do you prioritize tasks when working on multiple projects simultaneously?",
            "ideal_answer": "Methods: urgency vs impact matrix (Eisenhower), stakeholder communication for priority clarity, time blocking, task management tools (Jira, Trello, Notion), breaking large tasks into smaller milestones, proactively communicating delays, and knowing when to ask for help.",
            "keywords": ["prioritization", "time management", "stakeholder", "communication", "deadline", "eisenhower", "task", "focus", "tools"],
            "category": "general"
        },
        {
            "question": "Describe your ideal work environment and team culture.",
            "ideal_answer": "Good answers are specific: prefer collaborative vs independent, prefer structured vs autonomous, value psychological safety, continuous learning, direct feedback, diverse perspectives, and a balance of support and challenge. Align with what you know of the company culture.",
            "keywords": ["culture", "collaboration", "feedback", "autonomy", "learning", "team", "environment", "communication", "support"],
            "category": "general"
        },
    ],
    "Mixed": [
        {
            "question": "If you were to redesign a system you have previously built, what would you do differently?",
            "ideal_answer": "Answer should demonstrate reflection on past work: better initial requirements, choosing better tools/frameworks, improving scalability, adding observability/monitoring earlier, writing better tests, separating concerns more clearly. Shows growth mindset and engineering maturity.",
            "keywords": ["redesign", "improvement", "lessons", "scalability", "testing", "monitoring", "architecture", "reflection", "better"],
            "category": "general"
        },
    ],
}

# Keyword normalization aliases
KEYWORD_ALIASES = {
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "tf": "tensorflow",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "node": "node.js",
    "nodejs": "node.js",
}

def normalize_keyword(kw: str) -> str:
    """Normalize a keyword using aliases."""
    k = kw.lower().strip()
    return KEYWORD_ALIASES.get(k, k)

"""
practice_engine.py — Dedicated Practice Engine

Supports 4 Question Categories:
  1. Aptitude (Quantitative, logical, analytical, data interpretation, series, probability — 4-Option MCQs)
  2. Fundamental Concepts (Programming, OOP, DBMS, OS, Networks, Data Structures, Algorithms, Web)
  3. Problem Solving (Coding logic, debugging, algorithms, concurrency, system scenarios, complexity)
  4. Resume Based (Strictly grounded in candidate's uploaded resume skills, projects, and role)

Difficulty Levels: Easy, Medium, Hard.
Question Counts: 10, 20, 30.

Includes intelligent question tracking, MCQ support, problem-type rotation, & randomization:
  - Large curated question pools per category and difficulty tier
  - Aptitude MCQs with 4 options and server-verified correct answers
  - Problem Solving with categorized problem types (coding, debugging, algorithm, data_structure, complexity)
  - Deprioritizes recently served questions per user to guarantee variety across sessions
"""

import re
import hashlib
import random
import logging
from typing import List, Dict, Optional, Any, Set

from models.interview_engine import (
    evaluate_answer,
    _normalize_difficulty,
    _normalize_interview_type
)
from models.question_bank import (
    ROLE_QUESTION_BANK,
    SKILL_QUESTION_BANK,
    GENERAL_QUESTION_BANK,
    normalize_keyword
)

logger = logging.getLogger(__name__)

def generate_question_key(text: str) -> str:
    """Generate a stable 12-character hash for question deduplication."""
    clean = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    return hashlib.md5(clean.encode('utf-8')).hexdigest()[:12]


# 
# 1. APTITUDE QUESTION POOL (4-Option MCQs: Easy, Medium, Hard)
# 

APTITUDE_BANK = [
    # EASY (Arithmetic, basic logic, series, percentages, ratio, unitary method)
    {
        "question": "A train running at 54 km/h crosses a 150-meter-long platform in 20 seconds. What is the length of the train in meters?",
        "options": [
            "A. 120 meters",
            "B. 150 meters",
            "C. 180 meters",
            "D. 200 meters"
        ],
        "correct_option": "B",
        "ideal_answer": "Speed of train = 54 * (5/18) = 15 m/s. Total distance in 20 seconds = 15 * 20 = 300 meters. Total distance = Train Length + Platform Length. Therefore, Train Length = 300 - 150 = 150 meters.",
        "keywords": ["speed", "conversion", "15 m/s", "300 meters", "150 meters", "platform", "distance"],
        "category": "Time, Speed & Distance",
        "difficulty": "Easy"
    },
    {
        "question": "If an item is bought for $240 and sold at a profit of 25%, what is the selling price?",
        "options": [
            "A. $280",
            "B. $290",
            "C. $300",
            "D. $320"
        ],
        "correct_option": "C",
        "ideal_answer": "Profit = 25% of $240 = 0.25 * 240 = $60. Selling Price = Cost Price + Profit = $240 + $60 = $300.",
        "keywords": ["profit", "cost price", "selling price", "25%", "$60", "$300", "percentage"],
        "category": "Profit & Loss",
        "difficulty": "Easy"
    },
    {
        "question": "In a class of 60 students, the ratio of boys to girls is 3:2. How many girls are in the class?",
        "options": [
            "A. 20 girls",
            "B. 24 girls",
            "C. 30 girls",
            "D. 36 girls"
        ],
        "correct_option": "B",
        "ideal_answer": "Total parts = 3 + 2 = 5 parts. Value of 1 part = 60 / 5 = 12 students. Number of girls = 2 * 12 = 24 girls.",
        "keywords": ["ratio", "proportion", "5 parts", "12 students", "24 girls", "division"],
        "category": "Ratio & Proportion",
        "difficulty": "Easy"
    },
    {
        "question": "Find the next number in the sequence: 4, 9, 16, 25, 36, ___?",
        "options": [
            "A. 45",
            "B. 48",
            "C. 49",
            "D. 52"
        ],
        "correct_option": "C",
        "ideal_answer": "The sequence consists of consecutive perfect squares: 2^2=4, 3^2=9, 4^2=16, 5^2=25, 6^2=36. The next term is 7^2 = 49.",
        "keywords": ["series", "perfect squares", "consecutive", "49", "7 squared", "pattern"],
        "category": "Number Series",
        "difficulty": "Easy"
    },
    {
        "question": "A can finish a task in 12 days and B can finish the same task in 24 days. How many days will they take working together?",
        "options": [
            "A. 6 days",
            "B. 8 days",
            "C. 10 days",
            "D. 18 days"
        ],
        "correct_option": "B",
        "ideal_answer": "A's 1-day work = 1/12. B's 1-day work = 1/24. Combined 1-day work = 1/12 + 1/24 = 3/24 = 1/8. Together they will complete the task in 8 days.",
        "keywords": ["time and work", "1/12", "1/24", "1/8", "8 days", "combined rate"],
        "category": "Time & Work",
        "difficulty": "Easy"
    },
    {
        "question": "If 'LIGHT' is coded as 'MJHIU' by shifting each letter forward by 1 position in the alphabet, how is 'PLANT' coded?",
        "options": [
            "A. QMBOU",
            "B. QMCPU",
            "C. QLBOU",
            "D. QMBPV"
        ],
        "correct_option": "A",
        "ideal_answer": "Shifting each letter forward by +1: P->Q, L->M, A->B, N->O, T->U. Thus, PLANT is coded as 'QMBOU'.",
        "keywords": ["coding", "decoding", "alphabet shift", "letter pattern", "qmbou", "substitution"],
        "category": "Coding & Decoding",
        "difficulty": "Easy"
    },
    {
        "question": "The average of 5 consecutive integers is 28. What is the smallest of these integers?",
        "options": [
            "A. 24",
            "B. 26",
            "C. 27",
            "D. 28"
        ],
        "correct_option": "B",
        "ideal_answer": "For an odd count of consecutive integers, the average is the middle integer. So the middle integer is 28. The 5 consecutive integers are 26, 27, 28, 29, 30. The smallest integer is 26.",
        "keywords": ["average", "consecutive integers", "middle number", "28", "26", "smallest"],
        "category": "Quantitative Averages",
        "difficulty": "Easy"
    },
    {
        "question": "A single unbiased fair six-sided die is rolled. What is the probability of rolling a prime number?",
        "options": [
            "A. 1/6",
            "B. 1/3",
            "C. 1/2",
            "D. 2/3"
        ],
        "correct_option": "C",
        "ideal_answer": "The sample space is {1, 2, 3, 4, 5, 6} (6 outcomes). Prime outcomes are {2, 3, 5} (3 outcomes). Probability = 3/6 = 1/2 or 50%.",
        "keywords": ["probability", "dice", "prime numbers", "2, 3, 5", "3/6", "1/2", "50%"],
        "category": "Probability Basics",
        "difficulty": "Easy"
    },
    {
        "question": "A person walks 10 meters North, turns right and walks 10 meters East, then turns right again and walks 10 meters South. How far and in which direction is the person from the starting point?",
        "options": [
            "A. 10 meters North",
            "B. 10 meters East",
            "C. 10 meters South",
            "D. 20 meters East"
        ],
        "correct_option": "B",
        "ideal_answer": "North and South displacements cancel out (10 - 10 = 0). The remaining displacement is 10 meters due East.",
        "keywords": ["direction sense", "displacement", "10 meters", "east", "coordinates", "vector"],
        "category": "Logical Reasoning",
        "difficulty": "Easy"
    },
    {
        "question": "What is the simple interest on a principal of $5,000 invested at an annual interest rate of 6% for 3 years?",
        "options": [
            "A. $750",
            "B. $800",
            "C. $900",
            "D. $1,050"
        ],
        "correct_option": "C",
        "ideal_answer": "Simple Interest = (Principal * Rate * Time) / 100 = (5000 * 6 * 3) / 100 = $900.",
        "keywords": ["simple interest", "principal", "rate", "time", "p*r*t/100", "$900", "formula"],
        "category": "Simple Interest",
        "difficulty": "Easy"
    },
    {
        "question": "If 15 pens cost $45, what is the cost of 28 pens at the exact same unit price?",
        "options": [
            "A. $74",
            "B. $84",
            "C. $90",
            "D. $96"
        ],
        "correct_option": "B",
        "ideal_answer": "Unit price per pen = $45 / 15 = $3 per pen. Cost for 28 pens = 28 * $3 = $84.",
        "keywords": ["unitary method", "unit price", "$3", "28 pens", "$84", "arithmetic"],
        "category": "Quantitative Aptitude",
        "difficulty": "Easy"
    },
    {
        "question": "Find the missing number in the sequence: 2, 6, 12, 20, 30, 42, ___?",
        "options": [
            "A. 52",
            "B. 54",
            "C. 56",
            "D. 60"
        ],
        "correct_option": "C",
        "ideal_answer": "Differences between consecutive terms are +4, +6, +8, +10, +12. The next difference is +14. So 42 + 14 = 56 (Alternatively, n*(n+1): 7*8 = 56).",
        "keywords": ["series", "differences", "+14", "56", "n(n+1)", "pattern"],
        "category": "Number Series",
        "difficulty": "Easy"
    },

    # MEDIUM (Multi-step, relative speed, compound interest, arrangements, syllogisms)
    {
        "question": "A sum of money doubles itself in 5 years at simple interest. In how many years will it become 4 times itself at the exact same interest rate?",
        "options": [
            "A. 10 years",
            "B. 12 years",
            "C. 15 years",
            "D. 20 years"
        ],
        "correct_option": "C",
        "ideal_answer": "Money doubling means Interest = Principal (P) in 5 years, so Rate = 100/5 = 20% per year. To become 4 times itself, Interest must be 3P. Time = (3P * 100) / (P * 20) = 15 years.",
        "keywords": ["simple interest", "doubling", "rate 20%", "3p interest", "15 years", "multi-step"],
        "category": "Interest Calculations",
        "difficulty": "Medium"
    },
    {
        "question": "Two cars start simultaneously from points A and B 300 km apart, driving toward each other at 60 km/h and 40 km/h respectively. How long until they meet?",
        "options": [
            "A. 2.5 hours",
            "B. 3 hours",
            "C. 3.5 hours",
            "D. 4 hours"
        ],
        "correct_option": "B",
        "ideal_answer": "Relative speed moving toward each other = 60 + 40 = 100 km/h. Time to meet = Total Distance / Relative Speed = 300 / 100 = 3 hours.",
        "keywords": ["relative speed", "opposite directions", "100 km/h", "300 km", "3 hours", "time speed distance"],
        "category": "Time, Speed & Distance",
        "difficulty": "Medium"
    },
    {
        "question": "In how many distinct ways can the letters of the word 'LEADER' be arranged?",
        "options": [
            "A. 120 ways",
            "B. 360 ways",
            "C. 720 ways",
            "D. 1440 ways"
        ],
        "correct_option": "B",
        "ideal_answer": "Word has 6 letters with 'E' repeating 2 times. Total permutations = 6! / 2! = 720 / 2 = 360 distinct arrangements.",
        "keywords": ["permutations", "arrangements", "6 factorial", "2 factorial", "360 ways", "repetition"],
        "category": "Permutations & Combinations",
        "difficulty": "Medium"
    },
    {
        "question": "A bag contains 5 red balls, 4 blue balls, and 3 green balls (total 12). If 2 balls are drawn at random without replacement, what is the probability that both are red?",
        "options": [
            "A. 1/6",
            "B. 5/33",
            "C. 5/66",
            "D. 1/12"
        ],
        "correct_option": "B",
        "ideal_answer": "Total ways to choose 2 from 12 = 12C2 = (12 * 11) / 2 = 66. Ways to choose 2 red from 5 = 5C2 = (5 * 4) / 2 = 10. Probability = 10 / 66 = 5 / 33 (~15.15%).",
        "keywords": ["probability", "combinations", "12c2", "5c2", "66", "10/66", "5/33", "without replacement"],
        "category": "Probability",
        "difficulty": "Medium"
    },
    {
        "question": "Pipe A can fill a tank in 10 hours, and Pipe B can empty the full tank in 15 hours. If both pipes are opened simultaneously when the tank is empty, how many hours will it take to fill the tank?",
        "options": [
            "A. 20 hours",
            "B. 25 hours",
            "C. 30 hours",
            "D. 35 hours"
        ],
        "correct_option": "C",
        "ideal_answer": "Net filling rate per hour = (1/10) - (1/15) = (3 - 2)/30 = 1/30. Therefore, the tank will be completely filled in 30 hours.",
        "keywords": ["pipes and cisterns", "fill rate", "drain rate", "1/10 - 1/15", "1/30", "30 hours"],
        "category": "Time & Work",
        "difficulty": "Medium"
    },
    {
        "question": "A merchant marks up goods by 40% above cost price and then offers a discount of 20% on the marked price. What is the merchant's net profit percentage?",
        "options": [
            "A. 10%",
            "B. 12%",
            "C. 15%",
            "D. 20%"
        ],
        "correct_option": "B",
        "ideal_answer": "Let Cost Price = 100. Marked Price = 140. Discount = 20% of 140 = 28. Selling Price = 140 - 28 = 112. Net Profit = 112 - 100 = 12%.",
        "keywords": ["markup", "discount", "cost price 100", "marked price 140", "selling price 112", "12% profit"],
        "category": "Profit & Loss",
        "difficulty": "Medium"
    },
    {
        "question": "A mixture of 60 liters of milk and water contains 20% water. How many liters of pure water must be added to make the water content 40% in the new mixture?",
        "options": [
            "A. 15 liters",
            "B. 20 liters",
            "C. 24 liters",
            "D. 30 liters"
        ],
        "correct_option": "B",
        "ideal_answer": "Initial water = 20% of 60 = 12 L; milk = 48 L. In the new mixture, milk represents 60% of total volume. New total volume = 48 / 0.60 = 80 L. Water to add = 80 - 60 = 20 liters.",
        "keywords": ["mixtures", "alligation", "milk 48l", "water 12l", "new total 80l", "20 liters added"],
        "category": "Mixtures & Alligation",
        "difficulty": "Medium"
    },
    {
        "question": "If 8 men or 12 women can reap a field in 25 days, in how many days can 6 men and 11 women reap the same field?",
        "options": [
            "A. 12 days",
            "B. 15 days",
            "C. 18 days",
            "D. 20 days"
        ],
        "correct_option": "B",
        "ideal_answer": "Equivalence: 8 Men = 12 Women => 1 Man = 1.5 Women. Total workforce converted to women: 6 Men + 11 Women = (6 * 1.5) + 11 = 9 + 11 = 20 Women. Using M1*D1 = M2*D2: 12 * 25 = 20 * D2 => 300 = 20 * D2 => D2 = 15 days.",
        "keywords": ["men and women", "work equivalence", "8 men = 12 women", "20 women", "15 days", "time and work"],
        "category": "Time & Work",
        "difficulty": "Medium"
    },

    # HARD (Combinatorial optimization, Bayes probability, multi-stage rates, complex games)
    {
        "question": "A committee of 5 people is to be selected from 6 men and 4 women. What is the probability that the committee contains at least 3 women?",
        "options": [
            "A. 5/42",
            "B. 11/42",
            "C. 13/42",
            "D. 17/42"
        ],
        "correct_option": "B",
        "ideal_answer": "Total combinations = 10C5 = 252. Favorable cases: (1) Exactly 3 women & 2 men: 4C3 * 6C2 = 4 * 15 = 60. (2) Exactly 4 women & 1 man: 4C4 * 6C1 = 1 * 6 = 6. Total favorable = 60 + 6 = 66. Probability = 66 / 252 = 11 / 42 (~26.19%).",
        "keywords": ["combinations", "10c5 = 252", "4c3 * 6c2", "4c4 * 6c1", "66 favorable", "11/42", "at least 3"],
        "category": "Advanced Combinatorics",
        "difficulty": "Hard"
    },
    {
        "question": "Three machines A, B, and C produce 50%, 30%, and 20% of factory output with defect rates of 2%, 3%, and 4% respectively. If a randomly picked item is defective, what is the probability it was produced by Machine A?",
        "options": [
            "A. 8/27",
            "B. 10/27",
            "C. 12/27",
            "D. 15/27"
        ],
        "correct_option": "B",
        "ideal_answer": "Using Bayes' Theorem: P(Defect) = (0.50*0.02) + (0.30*0.03) + (0.20*0.04) = 0.010 + 0.009 + 0.008 = 0.027. P(A|Defect) = (0.50 * 0.02) / 0.027 = 0.010 / 0.027 = 10 / 27 (~37.04%).",
        "keywords": ["bayes theorem", "conditional probability", "prior probability", "0.027 total defect", "10/27", "machine a"],
        "category": "Probability & Statistics",
        "difficulty": "Hard"
    },
    {
        "question": "A, B, and C run on a circular track of circumference 1200 meters with speeds of 10 m/s, 15 m/s, and 20 m/s in the same direction from the same point. After what minimum time will all three meet again at the starting point?",
        "options": [
            "A. 180 seconds",
            "B. 200 seconds",
            "C. 240 seconds",
            "D. 300 seconds"
        ],
        "correct_option": "C",
        "ideal_answer": "Time taken by each to complete one full lap: A = 1200/10 = 120s, B = 1200/15 = 80s, C = 1200/20 = 60s. They will meet at the start point at LCM(120, 80, 60) = 240 seconds (4 minutes).",
        "keywords": ["circular track", "lap times", "120s, 80s, 60s", "lcm", "240 seconds", "4 minutes", "speed"],
        "category": "Time, Speed & Distance",
        "difficulty": "Hard"
    },
    {
        "question": "A vessel is completely filled with 80 liters of pure milk. 8 liters of milk is taken out and replaced with water. This process is repeated two more times (3 replacements total). How much pure milk remains in the vessel?",
        "options": [
            "A. 52.48 liters",
            "B. 56.00 liters",
            "C. 58.32 liters",
            "D. 60.12 liters"
        ],
        "correct_option": "C",
        "ideal_answer": "Formula: Remaining Liquid = Initial * (1 - x/V)^n. Here Initial = 80, x = 8, V = 80, n = 3. Remaining milk = 80 * (1 - 8/80)^3 = 80 * (0.9)^3 = 80 * 0.729 = 58.32 liters.",
        "keywords": ["successive replacement", "initial * (1 - x/v)^n", "(0.9)^3", "58.32 liters", "alligation"],
        "category": "Mixtures & Alligation",
        "difficulty": "Hard"
    },
    {
        "question": "In a tournament of 64 teams with single elimination format, how many total matches must be played to determine the champion?",
        "options": [
            "A. 62 matches",
            "B. 63 matches",
            "C. 64 matches",
            "D. 127 matches"
        ],
        "correct_option": "B",
        "ideal_answer": "Each match eliminates exactly 1 team. To determine 1 champion from 64 teams, 63 teams must be eliminated. Therefore, exactly 64 - 1 = 63 matches must be played.",
        "keywords": ["single elimination", "tournament", "n - 1", "63 matches", "elimination logic", "reasoning"],
        "category": "Logical & Analytical Reasoning",
        "difficulty": "Hard"
    }
]


# 
# 2. FUNDAMENTAL CONCEPTS QUESTION POOL (Easy, Medium, Hard)
# 

FUNDAMENTAL_CONCEPTS_BANK = [
    # EASY (Core OOP, basic SQL, networking basics, elementary data structures)
    {
        "question": "Describe the four fundamental pillars of Object-Oriented Programming (OOP) with a concise real-world software example for each.",
        "ideal_answer": "The four pillars are Encapsulation (hiding internal state with access modifiers), Abstraction (exposing clean interfaces while hiding implementation), Inheritance (code reuse across parent and child class hierarchies), and Polymorphism (methods behaving differently based on the runtime object instance).",
        "keywords": ["encapsulation", "abstraction", "inheritance", "polymorphism", "oop", "classes", "interfaces"],
        "category": "Object-Oriented Programming",
        "difficulty": "Easy"
    },
    {
        "question": "What is the difference between an Array and a Linked List in terms of memory layout and time complexity for insertion and index lookup?",
        "ideal_answer": "Arrays use contiguous memory allowing O(1) random index access but O(N) insertion/deletion due to element shifting. Linked lists use nodes with pointers scattered across heap memory, requiring O(N) sequential search for index lookup but allowing O(1) insertion if the target pointer is known.",
        "keywords": ["array", "linked list", "contiguous memory", "pointers", "o(1)", "o(n)", "lookup", "insertion"],
        "category": "Data Structures",
        "difficulty": "Easy"
    },
    {
        "question": "Explain the difference between SQL INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with expected query results.",
        "ideal_answer": "INNER JOIN returns only matching rows present in both tables. LEFT JOIN returns all rows from the left table and matched rows from the right table (filling NULLs for non-matches). FULL OUTER JOIN returns all rows from both tables, filling NULLs wherever a match is missing.",
        "keywords": ["inner join", "left join", "full outer join", "nulls", "sql", "relational database", "matching rows"],
        "category": "Database Management Systems",
        "difficulty": "Easy"
    },
    {
        "question": "What is the difference between TCP and UDP protocols, and when would an application choose UDP over TCP?",
        "ideal_answer": "TCP is connection-oriented, reliable, and guarantees ordered packet delivery via ACKs, retransmissions, and flow control. UDP is connectionless and stateless with minimal header overhead and lower latency, ideal for real-time video streaming, gaming, and VoIP where occasional packet loss is acceptable.",
        "keywords": ["tcp", "udp", "connection-oriented", "stateless", "packet loss", "latency", "handshake", "networking"],
        "category": "Computer Networks",
        "difficulty": "Easy"
    },
    {
        "question": "What are the common HTTP status code categories (2xx, 3xx, 4xx, 5xx) and what does each signify in web applications?",
        "ideal_answer": "2xx indicates Success (e.g. 200 OK, 201 Created); 3xx indicates Redirection (e.g. 301 Moved Permanently); 4xx indicates Client Errors (e.g. 400 Bad Request, 401 Unauthorized, 404 Not Found); 5xx indicates Server Errors (e.g. 500 Internal Error, 503 Service Unavailable).",
        "keywords": ["http", "2xx success", "3xx redirect", "4xx client error", "5xx server error", "rest", "status codes"],
        "category": "Web Architecture",
        "difficulty": "Easy"
    },
    {
        "question": "What is the difference between synchronous and asynchronous code execution in modern programming runtimes?",
        "ideal_answer": "Synchronous execution executes instructions sequentially, blocking subsequent tasks until current operations complete. Asynchronous execution offloads long-running I/O operations to background threads/event loops, allowing the main execution thread to process other tasks concurrently without blocking.",
        "keywords": ["synchronous", "asynchronous", "blocking", "non-blocking", "event loop", "concurrency", "i/o"],
        "category": "Programming Fundamentals",
        "difficulty": "Easy"
    },
    {
        "question": "What is a primary key and a foreign key in a relational database, and how do they enforce referential integrity?",
        "ideal_answer": "A primary key uniquely identifies each record in a table and cannot be NULL. A foreign key in a child table references the primary key of a parent table, enforcing referential integrity by preventing orphaned records and invalid parent references.",
        "keywords": ["primary key", "foreign key", "referential integrity", "unique", "not null", "relational database"],
        "category": "Database Management Systems",
        "difficulty": "Easy"
    },
    {
        "question": "What is the difference between Stack memory and Heap memory in application execution?",
        "ideal_answer": "Stack memory stores local primitive variables and function execution call frames with fast, automatic LIFO allocation and deallocation. Heap memory stores dynamically allocated objects with flexible lifecycles managed manually or via garbage collection, incurring higher allocation overhead.",
        "keywords": ["stack", "heap", "lifo", "local variables", "dynamic allocation", "garbage collection", "memory"],
        "category": "Computer Architecture & Memory",
        "difficulty": "Easy"
    },

    # MEDIUM (ACID, MVCC, Indexing, Concurrency, Normalization, OS scheduling)
    {
        "question": "Explain the ACID properties of database transactions and describe how isolation levels (Read Committed vs Repeatable Read) prevent dirty reads.",
        "ideal_answer": "ACID stands for Atomicity, Consistency, Isolation, and Durability. Isolation levels prevent concurrency anomalies: Read Committed ensures transactions only read committed data (eliminating dirty reads), while Repeatable Read uses snapshot isolation / row locks to prevent non-repeatable reads during transaction lifespan.",
        "keywords": ["acid", "atomicity", "consistency", "isolation", "durability", "dirty read", "non-repeatable read", "transactions"],
        "category": "Database Management Systems",
        "difficulty": "Medium"
    },
    {
        "question": "How do database B-Tree indexes accelerate search queries, and what is the computational trade-off during INSERT and UPDATE operations?",
        "ideal_answer": "B-Tree indexes maintain balanced multi-way search trees that reduce search disk I/O from O(N) table scans to O(log N) tree traversals. The trade-off is that every INSERT, UPDATE, or DELETE must rebalance nodes and update index leaves, increasing write amplification and write latency.",
        "keywords": ["b-tree", "indexing", "o(log n)", "table scan", "disk i/o", "write amplification", "insert overhead"],
        "category": "Database Management Systems",
        "difficulty": "Medium"
    },
    {
        "question": "Describe the four necessary conditions for a Deadlock to occur in operating systems and how resource preemption or lock ordering prevents it.",
        "ideal_answer": "The four Coffman conditions are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Deadlocks are prevented by breaking any single condition, commonly by enforcing a strict global lock acquisition hierarchy (eliminating Circular Wait) or using timeout preemption.",
        "keywords": ["deadlock", "coffman conditions", "mutual exclusion", "hold and wait", "no preemption", "circular wait", "lock ordering"],
        "category": "Operating Systems",
        "difficulty": "Medium"
    },
    {
        "question": "How does Virtual Memory work with Paging, Page Tables, and the Translation Lookaside Buffer (TLB)?",
        "ideal_answer": "Virtual memory maps virtual addresses to physical RAM frames via multi-level page tables managed by the MMU. The TLB acts as a high-speed hardware cache for page table translations. On a TLB miss, page tables are traversed; if the page is on disk, a Page Fault exception triggers OS swapping.",
        "keywords": ["virtual memory", "paging", "mmu", "tlb", "page table", "page fault", "hardware cache"],
        "category": "Operating Systems",
        "difficulty": "Medium"
    },
    {
        "question": "What is the difference between Process Context Switching and Thread Context Switching in terms of CPU register state, TLB invalidation, and overhead?",
        "ideal_answer": "Process context switches require saving CPU registers, switching page directory base registers (CR3 in x86), and invalidating/flushing the TLB cache, causing high overhead. Threads within the same process share virtual address space, requiring only register and stack pointer saves without TLB flushing.",
        "keywords": ["context switch", "process", "thread", "tlb flush", "page table", "registers", "overhead"],
        "category": "Operating Systems",
        "difficulty": "Medium"
    },
    {
        "question": "Explain the difference between Optimistic Concurrency Control (OCC) and Pessimistic Locking in concurrent database updates.",
        "ideal_answer": "Pessimistic locking acquires row or table locks before reading/modifying data (e.g., SELECT ... FOR UPDATE), blocking conflicting transactions. OCC assumes conflicts are rare, allows unhindered reads, and validates version timestamps during commit; if a concurrent update modified the row, the commit aborts and retries.",
        "keywords": ["optimistic locking", "pessimistic locking", "occ", "select for update", "version check", "concurrency"],
        "category": "Database Management Systems",
        "difficulty": "Medium"
    },

    # HARD (Distributed systems, consensus, CAP theorem, cache coherence, query engines)
    {
        "question": "Explain the CAP Theorem and explain why a distributed system can only guarantee at most two of Consistency, Availability, and Partition Tolerance simultaneously.",
        "ideal_answer": "Network partitions (P) are unavoidable in distributed networks. When a partition occurs, a system must choose between returning an immediate but potentially stale response to preserve Availability (AP system), or refusing/waiting to return only fully synchronized data at the cost of availability (CP system).",
        "keywords": ["cap theorem", "consistency", "availability", "partition tolerance", "network partition", "distributed consensus", "cp vs ap"],
        "category": "Distributed Systems",
        "difficulty": "Hard"
    },
    {
        "question": "How does the Raft Consensus Algorithm achieve leader election, log replication, and safety across distributed clusters?",
        "ideal_answer": "Raft decomposes consensus into Leader Election (heartbeats, election timeouts, randomized backoffs, term numbers), Log Replication (leader appends entries and commits upon majority ACK), and Safety (leaders must possess all previously committed entries to win election).",
        "keywords": ["raft", "consensus", "leader election", "log replication", "majority quorum", "terms", "heartbeats"],
        "category": "Distributed Systems",
        "difficulty": "Hard"
    },
    {
        "question": "How does Multi-Version Concurrency Control (MVCC) operate in PostgreSQL / InnoDB, and what are the implications for write amplification and VACUUM garbage collection?",
        "ideal_answer": "MVCC creates a new physical tuple version with xmin and xmax transaction IDs on UPDATE instead of modifying in-place. Readers view transaction snapshots without locking writers. Old dead tuple versions accumulate until cleaned up by VACUUM (or purge threads), introducing table bloat and write amplification.",
        "keywords": ["mvcc", "xmin xmax", "dead tuples", "vacuum", "table bloat", "write amplification", "snapshot isolation"],
        "category": "Database Management Systems",
        "difficulty": "Hard"
    },
    {
        "question": "What is the Cache Invalidation problem in distributed systems, and how do Write-Through, Write-Back, and Cache-Aside patterns handle cache consistency?",
        "ideal_answer": "Cache-Aside has the application read cache, query DB on miss, and invalidate cache on DB update. Write-Through updates cache and database synchronously. Write-Back writes to cache immediately and flushes asynchronously to DB (high write throughput, risk of data loss on crash).",
        "keywords": ["cache invalidation", "cache-aside", "write-through", "write-back", "eventual consistency", "ttl", "stale data"],
        "category": "System Architecture",
        "difficulty": "Hard"
    }
]


# 
# 3. PROBLEM SOLVING QUESTION POOL (Categorized Types: Easy, Medium, Hard)
# 

PROBLEM_SOLVING_BANK = [
    # EASY
    {
        "question": "Write a function `two_sum(nums, target)` that returns the indices of two numbers that add up to `target` in O(N) time complexity.",
        "ideal_answer": "```python\ndef two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in seen:\n            return [seen[diff], i]\n        seen[num] = i\n    return []\n```\nExplanation: Using a hash map stores visited numbers and their indices, allowing O(1) complement lookup in a single O(N) pass with O(N) auxiliary space.",
        "keywords": ["two sum", "hash map", "complement", "o(n) time", "single pass", "indices", "lookup"],
        "category": "Arrays & Hashing",
        "difficulty": "Easy",
        "problem_type": "coding"
    },
    {
        "question": "Debug the following function designed to check if a string is a palindrome. Identify the bug and provide the corrected code:\n```python\ndef is_palindrome(s):\n    s = s.lower()\n    for i in range(len(s)):\n        if s[i] != s[len(s) - i]:\n            return False\n    return True\n```",
        "ideal_answer": "Bug: `s[len(s) - i]` causes an `IndexError: string index out of range` on the first iteration when `i = 0` because indices are 0 to `len(s) - 1`.\n\nCorrected Code:\n```python\ndef is_palindrome(s):\n    s = s.lower()\n    n = len(s)\n    for i in range(n // 2):\n        if s[i] != s[n - 1 - i]:\n            return False\n    return True\n```",
        "keywords": ["index out of range", "off by one", "len(s) - 1 - i", "n // 2", "palindrome", "debugging"],
        "category": "Debugging",
        "difficulty": "Easy",
        "problem_type": "debugging"
    },
    {
        "question": "Explain the step-by-step algorithm to determine if a string containing '()', '[]', and '{}' is valid and balanced using a Stack.",
        "ideal_answer": "1. Initialize an empty stack and a bracket mapping `{')': '(', ']': '[', '}': '{'}`.\n2. Iterate through each character in the string.\n3. If the character is an opening bracket, push it onto the stack.\n4. If it is a closing bracket, check if the stack is non-empty and the popped element equals the matching opening bracket; if not, return False.\n5. Return True if the stack is completely empty at the end, False otherwise. Time: O(N), Space: O(N).",
        "keywords": ["stack", "balanced brackets", "parentheses", "push", "pop", "matching", "o(n)"],
        "category": "Stack & Strings",
        "difficulty": "Easy",
        "problem_type": "algorithm"
    },
    {
        "question": "Compare the data structure characteristics and memory layout of a Singly Linked List versus a Doubly Linked List. When is a Doubly Linked List preferred?",
        "ideal_answer": "A Singly Linked List node has `data` and `next` pointer. A Doubly Linked List node has `data`, `next`, and `prev` pointers. Doubly Linked Lists allow O(1) bi-directional traversal and O(1) node deletion when a node reference is provided (essential in LRU caches and deque implementations), at the cost of 1 additional pointer per node.",
        "keywords": ["singly linked list", "doubly linked list", "prev pointer", "bi-directional", "lru cache", "o(1) deletion"],
        "category": "Data Structures",
        "difficulty": "Easy",
        "problem_type": "data_structure"
    },
    {
        "question": "Analyze the time and space complexity of Linear Search vs Binary Search on an array of N sorted elements. Why does Binary Search require O(log N) time?",
        "ideal_answer": "Linear Search: Time O(N), Space O(1), inspecting each element sequentially.\nBinary Search: Time O(log N), Space O(1) iterative (or O(log N) recursive call stack).\nWhy O(log N): At each step, comparing the target with the middle element eliminates half of the remaining search space. The search space reduces as N, N/2, N/4 ... 1, requiring at most log2(N) comparisons.",
        "keywords": ["binary search", "linear search", "o(log n)", "o(n)", "divide and conquer", "halving", "log2(n)"],
        "category": "Algorithm Complexity",
        "difficulty": "Easy",
        "problem_type": "complexity"
    },
    {
        "question": "Write a function `reverse_string_in_place(chars)` that reverses a list of characters in-place using O(1) extra memory.",
        "ideal_answer": "```python\ndef reverse_string_in_place(chars):\n    left, right = 0, len(chars) - 1\n    while left < right:\n        chars[left], chars[right] = chars[right], chars[left]\n        left += 1\n        right -= 1\n    return chars\n```\nExplanation: The two-pointer approach swaps elements from outside inwards in O(N) time and O(1) auxiliary space.",
        "keywords": ["reverse in place", "two pointer", "swap", "left right", "o(1) space", "o(n) time"],
        "category": "Two Pointers",
        "difficulty": "Easy",
        "problem_type": "coding"
    },

    # MEDIUM
    {
        "question": "Write a function `length_of_longest_substring(s)` that returns the length of the longest substring without repeating characters in O(N) time.",
        "ideal_answer": "```python\ndef length_of_longest_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right, ch in enumerate(s):\n        if ch in char_map and char_map[ch] >= left:\n            left = char_map[ch] + 1\n        char_map[ch] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len\n```\nExplanation: Uses a sliding window with a hash map storing the latest index of each character. When a duplicate is seen, `left` shifts right past the previous occurrence in O(N) time.",
        "keywords": ["sliding window", "longest substring", "hash map", "character index", "left pointer", "o(n) time"],
        "category": "Sliding Window",
        "difficulty": "Medium",
        "problem_type": "coding"
    },
    {
        "question": "Debug this Binary Search implementation designed to find `target` in a sorted array `nums`. Identify the two bugs and fix them:\n```python\ndef binary_search(nums, target):\n    low = 0\n    high = len(nums)\n    while low < high:\n        mid = (low + high) / 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid\n        else:\n            high = mid\n    return -1\n```",
        "ideal_answer": "Bugs:\n1. `mid = (low + high) / 2` yields a float in Python 3; it must be integer division `//`.\n2. `low = mid` causes an infinite loop when `high - low == 1` and `nums[mid] < target`. Must be `low = mid + 1`.\n3. `high = len(nums)` with `high = mid` or `high = len(nums) - 1` with `high = mid - 1`.\n\nCorrected Code:\n```python\ndef binary_search(nums, target):\n    low, high = 0, len(nums) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n```",
        "keywords": ["integer division", "infinite loop", "mid + 1", "mid - 1", "binary search bug", "low <= high"],
        "category": "Debugging",
        "difficulty": "Medium",
        "problem_type": "debugging"
    },
    {
        "question": "Explain Floyd's Cycle Detection Algorithm (Tortoise and Hare) for detecting a loop in a Linked List. How do you find the exact node where the cycle begins?",
        "ideal_answer": "1. Initialize `slow = head` and `fast = head`.\n2. Advance `slow` by 1 step and `fast` by 2 steps. If `fast` or `fast.next` is None, there is no cycle.\n3. If `slow == fast`, a cycle exists.\n4. To find cycle start: Reset `slow = head` while leaving `fast` at meeting point. Advance both 1 step at a time (`slow = slow.next`, `fast = fast.next`). The node where they meet is the start of the cycle. Time: O(N), Space: O(1).",
        "keywords": ["floyd cycle", "tortoise and hare", "slow fast pointers", "meeting point", "cycle entry", "o(1) space"],
        "category": "Linked Lists & Pointers",
        "difficulty": "Medium",
        "problem_type": "algorithm"
    },
    {
        "question": "How do you design an LRU (Least Recently Used) Cache supporting `get(key)` and `put(key, value)` operations in O(1) time complexity?",
        "ideal_answer": "Combine a Hash Map with a Doubly Linked List.\n- Hash Map: Maps `key -> Node` for O(1) lookup.\n- Doubly Linked List: Stores nodes with dummy `head` (most recent) and `tail` (least recent).\n- `get(key)`: If key in map, move node to head and return value (O(1)).\n- `put(key, val)`: If key exists, update value and move node to head. If new key and capacity full, remove node before `tail` from both list and map; create new node and insert at `head` (O(1)).",
        "keywords": ["lru cache", "hash map", "doubly linked list", "dummy head tail", "o(1) get put", "eviction"],
        "category": "Data Structure Design",
        "difficulty": "Medium",
        "problem_type": "data_structure"
    },
    {
        "question": "Compare the asymptotic time and space complexities of QuickSort, MergeSort, and HeapSort in best, average, and worst cases. Why is QuickSort often preferred in practice?",
        "ideal_answer": "- MergeSort: Time O(N log N) always; Space O(N) auxiliary. Stable.\n- HeapSort: Time O(N log N) always; Space O(1) in-place. Unstable.\n- QuickSort: Time O(N log N) avg/best, O(N^2) worst (mitigated by randomized pivot); Space O(log N) stack. In-place.\nWhy QuickSort is preferred: In-place memory locality (cache friendliness), lower constant factors, and randomized/dual-pivot partitioning prevents worst-case scenarios.",
        "keywords": ["quicksort", "mergesort", "heapsort", "o(n log n)", "o(n^2)", "cache locality", "in-place", "stability"],
        "category": "Sorting Complexity",
        "difficulty": "Medium",
        "problem_type": "complexity"
    },

    # HARD
    {
        "question": "Write a function `trap_rain_water(height)` that calculates how much water an elevation map can trap after raining in O(N) time and O(1) auxiliary space.",
        "ideal_answer": "```python\ndef trap_rain_water(height):\n    if not height: return 0\n    left, right = 0, len(height) - 1\n    left_max, right_max = height[left], height[right]\n    water = 0\n    while left < right:\n        if left_max < right_max:\n            left += 1\n            left_max = max(left_max, height[left])\n            water += left_max - height[left]\n        else:\n            right -= 1\n            right_max = max(right_max, height[right])\n            water += right_max - height[right]\n    return water\n```\nExplanation: Two-pointer technique maintains running left and right bounds. Water trapped at any bar depends on `min(left_max, right_max) - height[i]`, achieving O(N) time and O(1) space.",
        "keywords": ["trapping rain water", "two pointers", "left_max right_max", "elevation map", "o(n) time", "o(1) space"],
        "category": "Dynamic Programming & Pointers",
        "difficulty": "Hard",
        "problem_type": "coding"
    },
    {
        "question": "Debug this multithreaded Python producer-consumer code experiencing race conditions and deadlocks:\n```python\nimport threading\nqueue = []\nlock = threading.Lock()\n\ndef producer(item):\n    lock.acquire()\n    queue.append(item)\n    # Missing notification\n\ndef consumer():\n    while True:\n        lock.acquire()\n        if len(queue) > 0:\n            item = queue.pop(0)\n            lock.release()\n            return item\n        # Deadlock: holds lock while waiting\n```",
        "ideal_answer": "Bugs:\n1. In `consumer()`, if the queue is empty, the loop does not release `lock`, starving `producer` and causing a permanent deadlock.\n2. Busy waiting in `consumer()` burns CPU cycles.\n\nCorrected implementation using `threading.Condition` or `queue.Queue`:\n```python\nimport threading\n\nclass BoundedBuffer:\n    def __init__(self):\n        self.queue = []\n        self.cond = threading.Condition()\n\n    def produce(self, item):\n        with self.cond:\n            self.queue.append(item)\n            self.cond.notify()\n\n    def consume(self):\n        with self.cond:\n            while not self.queue:\n                self.cond.wait()\n            return self.queue.pop(0)\n```",
        "keywords": ["deadlock", "race condition", "threading condition", "cond.wait", "cond.notify", "producer consumer", "busy wait"],
        "category": "Concurrency Debugging",
        "difficulty": "Hard",
        "problem_type": "debugging"
    },
    {
        "question": "How do you detect cycles and produce a valid execution order in a Directed Acyclic Graph (DAG) of microservice task dependencies using Topological Sort?",
        "ideal_answer": "Use Kahn's Algorithm (BFS) or Three-Color DFS:\n1. Kahn's Algorithm: Compute in-degree for all vertices. Enqueue nodes with in-degree 0. While queue non-empty, dequeue node, append to topological order, and decrement in-degree of its neighbors; if a neighbor reaches in-degree 0, enqueue it.\n2. Cycle Detection: If the count of processed nodes < total vertices, a cycle exists (dependencies cannot be resolved).\nTime: O(V + E), Space: O(V + E).",
        "keywords": ["topological sort", "kahn algorithm", "in-degree", "dag", "cycle detection", "bfs", "o(v+e)"],
        "category": "Graph Theory",
        "difficulty": "Hard",
        "problem_type": "algorithm"
    },
    {
        "question": "How does a Segment Tree or Fenwick Tree (Binary Indexed Tree) achieve O(log N) point updates and O(log N) range sum / min queries compared to a prefix sum array?",
        "ideal_answer": "- Prefix Sum Array: O(1) range queries, but O(N) point updates (inefficient for dynamic streams).\n- Segment Tree: Full binary tree representing intervals. Root covers `[0, N-1]`. Point update updates O(log N) tree ancestors. Range query aggregates O(log N) canonical non-overlapping segments.\n- Fenwick Tree: Compact array using bitwise `i & (-i)` lowest-set-bit transitions, achieving O(log N) prefix updates and queries with O(N) space and minimal constant factors.",
        "keywords": ["segment tree", "fenwick tree", "binary indexed tree", "range query", "point update", "o(log n)", "prefix sum"],
        "category": "Advanced Data Structures",
        "difficulty": "Hard",
        "problem_type": "data_structure"
    },
    {
        "question": "Analyze why Dijkstra's algorithm fails on graphs with negative edge weights and explain why the Bellman-Ford algorithm with O(V*E) complexity is required instead.",
        "ideal_answer": "Dijkstra's assumes once a node is visited/extracted from the priority queue, its shortest distance is finalized (greedy invariant). A negative edge later can retroactively shorten an already-settled path, violating correctness.\nBellman-Ford relaxes all E edges V-1 times. A V-th relaxation that still reduces distance detects a negative weight cycle. Time: O(V * E).",
        "keywords": ["dijkstra", "bellman ford", "negative edge weights", "negative cycle", "greedy invariant", "edge relaxation", "o(v*e)"],
        "category": "Graph Algorithm Complexity",
        "difficulty": "Hard",
        "problem_type": "complexity"
    }
]


# 
# 4. RESUME-BASED QUESTION TEMPLATES (Diverse Styles per Skill & Project)
# 

RESUME_SKILL_TEMPLATES = [
    {
        "template": "Explain how you design, optimize, and maintain code modules built with {skill} in production environments.",
        "ideal": "Best practices for {skill} involve modular design, adherence to clean architecture, comprehensive unit and integration testing, structured error handling, asynchronous non-blocking patterns where supported, and continuous profiling.",
        "keywords": ["{skill_lower}", "design", "production", "testing", "optimization", "error handling", "maintainability"],
        "category": "Skill Architecture"
    },
    {
        "template": "What are the common performance bottlenecks, memory management challenges, or concurrency issues when utilizing {skill} at scale?",
        "ideal": "Common bottlenecks in {skill} include excessive I/O blocking, unindexed query latency, memory leaks from retained references, improper thread synchronization, or lack of caching. Mitigations include connection pooling, profiling, and caching layers.",
        "keywords": ["{skill_lower}", "bottlenecks", "concurrency", "memory", "scaling", "profiling", "latency"],
        "category": "Skill Performance"
    },
    {
        "template": "Can you walk through a challenging debugging scenario or architecture trade-off you solved while working with {skill}?",
        "ideal": "A systematic debugging approach involves isolating the failure via logs and stack traces, reproducing edge cases with regression tests, analyzing trade-offs between compute and storage or simplicity vs performance, and deploying a validated fix.",
        "keywords": ["{skill_lower}", "debugging", "trade-off", "root cause", "resolution", "testing", "edge cases"],
        "category": "Skill Troubleshooting"
    },
    {
        "template": "How do you implement security best practices and input validation when building backend services or data flows using {skill}?",
        "ideal": "Security practices for {skill} include rigorous input sanitization, parameterized queries to prevent injection, role-based access control, cryptographic secret management, rate limiting, and dependency vulnerability scanning.",
        "keywords": ["{skill_lower}", "security", "validation", "injection", "access control", "sanitization", "authentication"],
        "category": "Skill Security"
    },
    {
        "template": "How do you test and automate integration pipelines for applications leveraging {skill} before production release?",
        "ideal": "Testing strategies encompass automated unit tests with mocks, integration testing with containerized databases/services, load testing under peak traffic thresholds, and CI/CD pipelines with automated smoke tests and rollback mechanisms.",
        "keywords": ["{skill_lower}", "unit tests", "integration", "ci/cd", "automation", "mocking", "pipeline"],
        "category": "Skill QA & Testing"
    }
]

RESUME_PROJECT_TEMPLATES = [
    {
        "template": "In your project '{project}', what was the primary architectural design pattern chosen and what trade-offs did it present?",
        "ideal": "The architectural approach balanced modularity, separation of concerns, scalability, and ease of deployment, allowing decoupled services and reliable data pipelines.",
        "keywords": ["architecture", "design pattern", "scalability", "modularity", "trade-off", "performance", "clean code"],
        "category": "Project Architecture"
    },
    {
        "template": "How did you measure throughput, latency, accuracy, or user satisfaction in your project '{project}'?",
        "ideal": "Success metrics included response latency reduction, uptime reliability, model evaluation metrics (F1-score, accuracy, precision/recall), user satisfaction, and automated test coverage.",
        "keywords": ["metrics", "evaluation", "throughput", "latency", "accuracy", "testing", "monitoring"],
        "category": "Project Evaluation"
    },
    {
        "template": "What was the most significant technical challenge you encountered while building '{project}' and how did you resolve it?",
        "ideal": "The technical obstacle was resolved by profiling root cause bottlenecks, refactoring critical code paths, implementing proper caching/indexing, and verifying stability through load testing.",
        "keywords": ["technical challenge", "root cause", "refactoring", "bottleneck", "stability", "resolution"],
        "category": "Project Problem Solving"
    }
]


# 
# 5. MAIN PRACTICE QUESTION GENERATOR (With Randomization, MCQ & Type Rotation)
# 

def generate_practice_questions(
    resume_text: str = "",
    skills: List[str] = None,
    predicted_role: str = "Software Engineer",
    question_count: int = 10,
    difficulty: str = "Medium",
    practice_type: str = "Technical",
    job_description: Optional[str] = None,
    question_source: str = "resume_based",
    recently_served_keys: Optional[Set[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate exactly 10, 20, or 30 questions with:
      - 4 Categories: 'aptitude', 'fundamental_concepts', 'problem_solving', 'resume_based'
      - Difficulty Scaling: Easy, Medium, Hard
      - Aptitude MCQs (4 options with correct_option)
      - Problem Solving with alternating problem types (coding, debugging, algorithm, data_structure, complexity)
      - Randomization that prioritizes questions not recently served to this user
    """
    if skills is None:
        skills = []
    if recently_served_keys is None:
        recently_served_keys = set()

    question_count = int(question_count)
    if question_count not in [10, 20, 30]:
        if question_count <= 15:
            question_count = 10
        elif question_count <= 25:
            question_count = 20
        else:
            question_count = 30

    norm_difficulty = _normalize_difficulty(difficulty)
    norm_type = _normalize_interview_type(practice_type)

    candidate_pool: List[Dict[str, Any]] = []
    seen_hashes: Set[str] = set()

    def add_to_pool(q_item: Dict[str, Any]):
        q_text = q_item["question"].strip()
        q_key = generate_question_key(q_text)
        if q_key not in seen_hashes:
            seen_hashes.add(q_key)
            item_copy = dict(q_item)
            item_copy["question_key"] = q_key
            candidate_pool.append(item_copy)

    # 
    # BRANCH 1: APTITUDE (4-Option MCQs)
    # 
    if question_source == "aptitude":
        for item in APTITUDE_BANK:
            if item.get("difficulty", "Medium").lower() == norm_difficulty.lower():
                add_to_pool({
                    "question": item["question"],
                    "ideal_answer": item["ideal_answer"],
                    "keywords": item["keywords"],
                    "options": item.get("options", []),
                    "correct_option": item.get("correct_option", ""),
                    "question_type": "Aptitude",
                    "category": item["category"],
                    "difficulty": norm_difficulty
                })
        for item in APTITUDE_BANK:
            add_to_pool({
                "question": item["question"],
                "ideal_answer": item["ideal_answer"],
                "keywords": item["keywords"],
                "options": item.get("options", []),
                "correct_option": item.get("correct_option", ""),
                "question_type": "Aptitude",
                "category": item["category"],
                "difficulty": item.get("difficulty", norm_difficulty)
            })

    # 
    # BRANCH 2: FUNDAMENTAL CONCEPTS
    # 
    elif question_source == "fundamental_concepts":
        for item in FUNDAMENTAL_CONCEPTS_BANK:
            if item.get("difficulty", "Medium").lower() == norm_difficulty.lower():
                add_to_pool({
                    "question": item["question"],
                    "ideal_answer": item["ideal_answer"],
                    "keywords": item["keywords"],
                    "question_type": "Technical",
                    "category": item["category"],
                    "difficulty": norm_difficulty
                })
        role_bank = ROLE_QUESTION_BANK.get(predicted_role, {})
        for q in role_bank.get("Technical", {}).get(norm_difficulty, []):
            add_to_pool({
                "question": q["question"],
                "ideal_answer": q["ideal_answer"],
                "keywords": q["keywords"],
                "question_type": "Technical",
                "category": f"Fundamentals: {predicted_role}",
                "difficulty": norm_difficulty
            })
        for item in FUNDAMENTAL_CONCEPTS_BANK:
            add_to_pool({
                "question": item["question"],
                "ideal_answer": item["ideal_answer"],
                "keywords": item["keywords"],
                "question_type": "Technical",
                "category": item["category"],
                "difficulty": item.get("difficulty", norm_difficulty)
            })

    # 
    # BRANCH 3: PROBLEM SOLVING (With Alternating Problem Types)
    # 
    elif question_source == "problem_solving":
        for item in PROBLEM_SOLVING_BANK:
            if item.get("difficulty", "Medium").lower() == norm_difficulty.lower():
                add_to_pool({
                    "question": item["question"],
                    "ideal_answer": item["ideal_answer"],
                    "keywords": item["keywords"],
                    "problem_type": item.get("problem_type", "algorithm"),
                    "question_type": "Technical",
                    "category": item["category"],
                    "difficulty": norm_difficulty
                })
        for item in PROBLEM_SOLVING_BANK:
            add_to_pool({
                "question": item["question"],
                "ideal_answer": item["ideal_answer"],
                "keywords": item["keywords"],
                "problem_type": item.get("problem_type", "algorithm"),
                "question_type": "Technical",
                "category": item["category"],
                "difficulty": item.get("difficulty", norm_difficulty)
            })

    # 
    # BRANCH 4: RESUME BASED (Strictly Grounded)
    # 
    else:
        for s in skills:
            norm_s = normalize_keyword(s)
            for cand_key in [s, norm_s, s.lower()]:
                if cand_key in SKILL_QUESTION_BANK:
                    for bank_q in SKILL_QUESTION_BANK[cand_key]:
                        add_to_pool({
                            "question": bank_q["question"],
                            "ideal_answer": bank_q["ideal_answer"],
                            "keywords": bank_q["keywords"],
                            "question_type": "Technical",
                            "category": f"Skill: {s}",
                            "difficulty": norm_difficulty
                        })

        project_matches = re.findall(
            r'(?:PROJECTS|PERSONAL PROJECTS)[\s:]*\n([\s\S]{30,500}?)(?=\n\s*(?:EXPERIENCE|WORK|EDUCATION|SKILLS|CERTIFICATIONS|$))',
            resume_text,
            re.IGNORECASE
        )
        if project_matches:
            proj_lines = [l.strip().lstrip('•-*123456789. ') for l in project_matches[0].splitlines() if len(l.strip()) > 10][:4]
            for proj_title in proj_lines:
                clean_title = proj_title.split(':')[0].split('-')[0].strip()
                if len(clean_title) > 3:
                    for pt in RESUME_PROJECT_TEMPLATES:
                        q_text = pt["template"].format(project=clean_title)
                        add_to_pool({
                            "question": q_text,
                            "ideal_answer": pt["ideal"],
                            "keywords": pt["keywords"] + [clean_title.lower()],
                            "question_type": "Technical",
                            "category": f"Project: {clean_title}",
                            "difficulty": norm_difficulty
                        })

        for skill_name in skills:
            s_clean = skill_name.strip()
            s_lower = s_clean.lower()
            for template_obj in RESUME_SKILL_TEMPLATES:
                q_text = template_obj["template"].format(skill=s_clean)
                ideal_text = template_obj["ideal"].format(skill=s_clean)
                kws = [k.format(skill_lower=s_lower) for k in template_obj["keywords"]]
                add_to_pool({
                    "question": q_text,
                    "ideal_answer": ideal_text,
                    "keywords": kws,
                    "question_type": "Technical",
                    "category": f"Deep Dive: {s_clean}",
                    "difficulty": norm_difficulty
                })

        role_bank = ROLE_QUESTION_BANK.get(predicted_role, {})
        if not role_bank:
            for rk in ROLE_QUESTION_BANK:
                if rk.lower() in predicted_role.lower() or predicted_role.lower() in rk.lower():
                    role_bank = ROLE_QUESTION_BANK[rk]
                    break

        if role_bank:
            type_dict = role_bank.get(norm_type, {})
            if not type_dict:
                type_dict = role_bank.get("Technical", {})
            diff_qs = type_dict.get(norm_difficulty, [])
            for q in diff_qs:
                add_to_pool({
                    "question": q["question"],
                    "ideal_answer": q["ideal_answer"],
                    "keywords": q["keywords"],
                    "question_type": norm_type,
                    "category": f"Role: {predicted_role}",
                    "difficulty": norm_difficulty
                })

    # 
    # SELECTION & TYPE ROTATION ALGORITHM
    # 
    unseen_pool = [q for q in candidate_pool if q["question_key"] not in recently_served_keys]
    seen_pool = [q for q in candidate_pool if q["question_key"] in recently_served_keys]

    random.shuffle(unseen_pool)
    random.shuffle(seen_pool)

    raw_selected: List[Dict[str, Any]] = []

    if question_source == "problem_solving":
        # Interleave problem types (coding, debugging, algorithm, data_structure, complexity)
        types_order = ["coding", "debugging", "algorithm", "data_structure", "complexity"]
        by_type: Dict[str, List[Dict[str, Any]]] = {t: [] for t in types_order}
        
        # Combine unseen + seen in order
        combined_pool = unseen_pool + seen_pool
        for q in combined_pool:
            ptype = q.get("problem_type", "algorithm")
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append(q)

        # Round-robin selection across problem types
        idx = 0
        while len(raw_selected) < question_count and any(by_type.values()):
            current_type = types_order[idx % len(types_order)]
            if by_type.get(current_type):
                raw_selected.append(by_type[current_type].pop(0))
            idx += 1
            if all(len(v) == 0 for v in by_type.values()):
                break
    else:
        if len(unseen_pool) >= question_count:
            raw_selected = unseen_pool[:question_count]
        else:
            needed = question_count - len(unseen_pool)
            raw_selected = unseen_pool + seen_pool[:needed]

    # If still fewer than requested, backfill from general bank
    if len(raw_selected) < question_count:
        for gen_type in [norm_type, "Technical", "Behavioral"]:
            if gen_type in GENERAL_QUESTION_BANK:
                for gq in GENERAL_QUESTION_BANK[gen_type]:
                    if len(raw_selected) >= question_count:
                        break
                    g_key = generate_question_key(gq["question"])
                    if g_key not in [q["question_key"] for q in raw_selected]:
                        raw_selected.append({
                            "question": gq["question"],
                            "ideal_answer": gq["ideal_answer"],
                            "keywords": gq["keywords"],
                            "question_type": gen_type,
                            "category": f"General {gen_type}",
                            "difficulty": norm_difficulty,
                            "question_key": g_key
                        })

    final_selection = raw_selected[:question_count]

    for idx, item in enumerate(final_selection):
        item["order_index"] = idx + 1

    return final_selection


def calculate_practice_report(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate performance metrics from answered practice questions.
    """
    if not answers:
        return {
            "overall_score": 0.0,
            "avg_semantic_score": 0.0,
            "avg_keyword_score": 0.0,
            "strengths": ["Practice session initiated"],
            "improvement_areas": ["Complete more questions for detailed performance analysis"],
            "total_answered": 0
        }

    semantic_scores = [a["semantic_score"] for a in answers if "semantic_score" in a]
    keyword_scores = [a["keyword_score"] for a in answers if "keyword_score" in a]
    combined_scores = [a["combined_score"] for a in answers if "combined_score" in a]

    avg_sem = float(sum(semantic_scores) / len(semantic_scores)) if semantic_scores else 0.0
    avg_kw = float(sum(keyword_scores) / len(keyword_scores)) if keyword_scores else 0.0
    overall = float(sum(combined_scores) / len(combined_scores)) if combined_scores else 0.0

    strengths = []
    improvements = []

    if avg_sem >= 75.0:
        strengths.append("High conceptual accuracy and well-structured explanations.")
    elif avg_sem >= 55.0:
        strengths.append("Solid fundamental understanding across tested technical concepts.")
    else:
        improvements.append("Expand on foundational principles and step-by-step reasoning.")

    if avg_kw >= 70.0:
        strengths.append("Effective use of precise industry terminology and keywords.")
    else:
        improvements.append("Include more standard technical terminology and architectural concepts.")

    strong_qs = [a for a in answers if a.get("combined_score", 0) >= 75.0]
    weak_qs = [a for a in answers if a.get("combined_score", 0) < 60.0]

    if strong_qs:
        strengths.append(f"Demonstrated mastery on {len(strong_qs)} practice questions.")
    if weak_qs:
        improvements.append(f"Review and reinforce topics for {len(weak_qs)} questions scored under 60%.")

    earned_marks = sum(a.get("marks_awarded", 0) for a in answers)
    total_marks = sum(a.get("max_marks", 2) for a in answers)
    correct_count = sum(1 for a in answers if a.get("is_correct") is True or (a.get("is_correct") is None and a.get("combined_score", 0) >= 50.0))
    wrong_count = len(answers) - correct_count

    return {
        "overall_score": round(overall, 1),
        "avg_semantic_score": round(avg_sem, 1),
        "avg_keyword_score": round(avg_kw, 1),
        "earned_marks": earned_marks,
        "total_marks": total_marks,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "strengths": strengths,
        "improvement_areas": improvements,
        "total_answered": len(answers)
    }

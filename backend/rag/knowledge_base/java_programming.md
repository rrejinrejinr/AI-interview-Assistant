# Java Programming Language and Architecture

## What is Java
Java is a high-level, class-based, object-oriented, strongly typed programming language designed with the philosophy "Write Once, Run Anywhere" (WORA).
Java source code (`.java`) is compiled by `javac` into platform-independent bytecode (`.class`), which is executed by the Java Virtual Machine (JVM).

Core Java Characteristics:
1. Object-Oriented: Encapsulation, Inheritance, Polymorphism, Abstraction.
2. Platform Independence: Bytecode runs on any operating system with a compatible JVM.
3. Automatic Memory Management: Garbage Collector (GC) automatically reclaims unused heap memory.
4. Multithreading & Concurrency: Built-in thread support, synchronized blocks, `java.util.concurrent`.
5. Robust & Secure: Strong type checking, exception handling, and bytecode verifier.

## Java Platform Components: JDK, JRE, and JVM
- JVM (Java Virtual Machine): Executes bytecode, manages runtime memory (Heap, Stack, Metaspace), and performs JIT (Just-In-Time) compilation and Garbage Collection.
- JRE (Java Runtime Environment): Includes the JVM plus core runtime libraries necessary to execute Java applications.
- JDK (Java Development Kit): Full development environment containing the JRE, compiler (`javac`), debugger (`jdb`), and development tools.

## Java Collections Framework: ArrayList vs LinkedList
- ArrayList: Backed by a dynamically resizing contiguous array.
  - Fast O(1) random access via `get(index)`.
  - Slower O(n) insertions/deletions in the middle due to element shifting.
  - Cache-friendly contiguous memory locality.
- LinkedList: Backed by a doubly-linked list of nodes.
  - O(n) sequential traversal to access an element.
  - O(1) insertion/deletion once the node position is located.
  - Higher memory overhead due to `prev` and `next` object references.

## OOP Polymorphism in Java
Polymorphism allows objects to be treated as instances of their parent class or interface.
1. Compile-Time Polymorphism (Method Overloading): Multiple methods with the same name but different argument signatures.
2. Runtime Polymorphism (Method Overriding): A subclass provides its specific implementation of a superclass method, resolved dynamically at runtime using virtual method invocation.

# Web APIs, Architecture and Networking

## What is an API (Application Programming Interface)
An Application Programming Interface (API) is a formal set of protocols, routines, and tools that allows different software applications to communicate and exchange data with one another.
APIs abstract underlying implementation complexity, exposing well-defined contracts (endpoints, request/response formats, status codes).

Key API Architectural Styles:
1. REST (Representational State Transfer): Uses standard HTTP methods (GET, POST, PUT, DELETE, PATCH), stateless communication, and JSON payloads.
2. GraphQL: Query language allowing clients to request exactly the fields they need in a single endpoint request.
3. gRPC: High-performance, binary RPC framework using Protocol Buffers and HTTP/2 transport.
4. WebSockets: Full-duplex, persistent bidirectional communication over a single TCP connection.

## RESTful API Design Principles
- Statelessness: Each request from client to server must contain all information needed to understand and process the request. No client context is stored on the server.
- Standard HTTP Methods:
  - `GET`: Retrieve resource representation (idempotent, safe).
  - `POST`: Create a new resource (non-idempotent).
  - `PUT`: Replace resource completely (idempotent).
  - `PATCH`: Partially update resource.
  - `DELETE`: Remove resource (idempotent).
- Standard HTTP Status Codes:
  - 2xx Success (200 OK, 201 Created, 204 No Content).
  - 4xx Client Error (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found).
  - 5xx Server Error (500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable).

## JWT Authentication and Stateless Security
JSON Web Token (JWT) is an open standard (RFC 7519) for transmitting secure claims between parties.
Structure: `Header.Payload.Signature`
- Header: Algorithm (`HS256`, `RS256`) and token type (`JWT`).
- Payload: Claims containing user identity, roles, expiration timestamp (`exp`).
- Signature: Cryptographic hash verifying authenticity and tamper-proofing.
Stateless Nature: The server verifies the signature mathematically without performing database lookups for session state on every request.

## Computer Networks: TCP vs UDP
- TCP (Transmission Control Protocol): Connection-oriented protocol using a 3-way handshake (SYN, SYN-ACK, ACK), guaranteeing reliable, ordered packet delivery with flow and congestion control.
- UDP (User Datagram Protocol): Connectionless, lightweight protocol with minimal header overhead, suited for low-latency streaming, VoIP, gaming, and DNS.

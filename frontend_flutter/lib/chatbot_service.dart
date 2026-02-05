import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;

/// ChatMessage model to represent a single message in the conversation
class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.isUser,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'text': text,
        'isUser': isUser,
        'timestamp': timestamp.toIso8601String(),
      };
}

/// ChatbotService handles all chatbot-related functionality
/// Connects to the backend Gemini-powered /chat endpoint
class ChatbotService {
  // Backend URL - same as ApiService
  static const String baseUrl = "http://localhost:8001";

  // Message history for the current session
  final List<ChatMessage> _messages = [];

  // Contract context from the analysis
  Map<String, dynamic>? _contractContext;

  // Loading state
  bool _isLoading = false;

  // Getters
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  bool get hasContext => _contractContext != null;

  /// Set the contract context from the analysis result
  /// This feeds the chatbot with all the extracted contract data
  void setContractContext(Map<String, dynamic>? analysisResult) {
    _contractContext = analysisResult;
    // Clear previous messages when new contract is loaded
    _messages.clear();

    // Add a welcome message when context is set
    if (analysisResult != null) {
      _messages.add(ChatMessage(
        text:
            "I've analyzed your contract. Ask me anything about the lease terms, vehicle details, or risk analysis!",
        isUser: false,
      ));
    }
  }

  /// Clear the chat history
  void clearMessages() {
    _messages.clear();
  }

  /// Clear everything (messages and context)
  void reset() {
    _messages.clear();
    _contractContext = null;
  }

  /// Send a message to the AI and get a response
  /// Returns the AI's reply text
  Future<String> sendMessage(String userMessage) async {
    if (userMessage.trim().isEmpty) {
      throw Exception("Message cannot be empty");
    }

    // Add user message to history
    _messages.add(ChatMessage(
      text: userMessage,
      isUser: true,
    ));

    _isLoading = true;

    try {
      final reply = await _callChatApi(userMessage);

      // Add AI response to history
      _messages.add(ChatMessage(
        text: reply,
        isUser: false,
      ));

      _isLoading = false;
      return reply;
    } catch (e) {
      _isLoading = false;

      // Add error message to chat
      final errorMsg = "Sorry, I couldn't process your request. ${e.toString()}";
      _messages.add(ChatMessage(
        text: errorMsg,
        isUser: false,
      ));

      rethrow;
    }
  }

  /// Internal method to call the backend /chat API
  Future<String> _callChatApi(String message) async {
    final uri = Uri.parse("$baseUrl/chat");

    try {
      final response = await http
          .post(
            uri,
            headers: {"Content-Type": "application/json"},
            body: jsonEncode({
              "message": message,
              "context": _contractContext ?? {},
            }),
          )
          .timeout(const Duration(seconds: 60));

      if (response.statusCode != 200) {
        try {
          final errorBody = jsonDecode(response.body);
          throw Exception(
              errorBody["detail"] ?? errorBody["error"] ?? "Chat request failed");
        } catch (_) {
          throw Exception(
              "Server error: ${response.statusCode} ${response.reasonPhrase}");
        }
      }

      final decoded = jsonDecode(response.body);

      if (decoded["status"] != "success") {
        throw Exception(decoded["error"] ?? "Chat error");
      }

      return decoded["reply"] ?? "No reply received.";
    } on http.ClientException {
      throw Exception("Unable to connect to backend. Is FastAPI running?");
    } on TimeoutException {
      throw Exception("Chat request timed out.");
    } catch (e) {
      throw Exception("Chat error: ${e.toString()}");
    }
  }

  /// Get a summary of the contract context for display
  String getContextSummary() {
    if (_contractContext == null) {
      return "No contract loaded. Upload a PDF to enable the assistant.";
    }

    final sla = _contractContext!["sla_fields"];
    if (sla == null) return "Contract loaded but no details available.";

    final vehicle = sla["vehicle"] ?? {};
    final financial = sla["financial"] ?? {};

    return "Contract: ${vehicle["make"] ?? "Unknown"} ${vehicle["model"] ?? ""} - "
        "${financial["monthly_rental"] ?? "N/A"}/month";
  }
}


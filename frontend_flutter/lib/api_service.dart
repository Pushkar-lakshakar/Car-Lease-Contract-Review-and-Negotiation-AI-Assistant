import 'dart:convert';
import 'dart:typed_data';
import 'dart:async';
import 'package:http/http.dart' as http;

class ApiService {
  // Change this if deploying
  static const String baseUrl = "http://localhost:8001";

  // User session
  static String? currentUserId;
  static String? currentUsername;

  // ==============================
  // PDF ANALYSIS
  // ==============================
  static Future<Map<String, dynamic>> analyzePdf(
    Uint8List fileBytes,
    String fileName,
  ) async {
    final uri = Uri.parse("$baseUrl/analyze");
    if (currentUserId != null) {
      uri.replace(queryParameters: {"user_id": currentUserId});
    }

    var request = http.MultipartRequest("POST", currentUserId != null 
      ? Uri.parse("$baseUrl/analyze?user_id=$currentUserId")
      : uri);

    request.files.add(
      http.MultipartFile.fromBytes(
        "pdf",
        fileBytes,
        filename: fileName,
      ),
    );

    try {
      final streamedResponse =
          await request.send().timeout(const Duration(seconds: 60));

      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode != 200) {
        try {
          final errorBody = jsonDecode(response.body);
          throw Exception(errorBody["detail"] ?? "Processing failed");
        } catch (_) {
          throw Exception(
              "Server error: ${response.statusCode} ${response.reasonPhrase}");
        }
      }

      final decoded = jsonDecode(response.body);

      if (decoded["status"] == "error") {
        throw Exception(decoded["error"] ?? "Analysis failed");
      }

      return decoded;
    } on http.ClientException {
      throw Exception(
          "Unable to connect to backend. Is FastAPI running?");
    } on TimeoutException {
      throw Exception("Request timed out while analyzing PDF.");
    } catch (e) {
      throw Exception("Error: ${e.toString()}");
    }
  }

  // ==============================
  // HEALTH CHECK
  // ==============================
  static Future<Map<String, dynamic>> healthCheck() async {
    final uri = Uri.parse("$baseUrl/health");

    try {
      final response =
          await http.get(uri).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception("Backend not healthy");
      }

      return jsonDecode(response.body);
    } on http.ClientException {
      throw Exception("Unable to connect to backend.");
    } on TimeoutException {
      throw Exception("Health check timed out.");
    } catch (e) {
      throw Exception("Health check failed: ${e.toString()}");
    }
  }

  // ==============================
  // CHAT WITH BACKEND
  // ==============================
  static Future<String> sendChatMessage(
    String message,
    Map<String, dynamic>? context,
  ) async {
    final uri = Uri.parse("$baseUrl/chat");

    try {
      final response = await http
          .post(
            uri,
            headers: {"Content-Type": "application/json"},
            body: jsonEncode({
              "message": message,
              "context": context ?? {},
            }),
          )
          .timeout(const Duration(seconds: 60));

      if (response.statusCode != 200) {
        try {
          final errorBody = jsonDecode(response.body);
          throw Exception(
              errorBody["detail"] ??
                  errorBody["error"] ??
                  "Chat request failed");
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
      throw Exception(
          "Unable to connect to backend. Is FastAPI running?");
    } on TimeoutException {
      throw Exception("Chat request timed out.");
    } catch (e) {
      throw Exception("Chat error: ${e.toString()}");
    }
  }

  // ==============================
  // HISTORY
  // ==============================
  static Future<List<dynamic>> getHistory() async {
    final query = currentUserId != null ? "?user_id=$currentUserId" : "";
    final uri = Uri.parse("$baseUrl/history$query");

    try {
      final response =
          await http.get(uri).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception("Failed to load history");
      }

      return jsonDecode(response.body);
    } on http.ClientException {
      throw Exception("Unable to connect to backend.");
    } on TimeoutException {
      throw Exception("History request timed out.");
    } catch (e) {
      throw Exception("History error: ${e.toString()}");
    }
  }

  static Future<Map<String, dynamic>> getHistoryDetail(String id) async {
    final uri = Uri.parse("$baseUrl/history/$id");

    try {
      final response =
          await http.get(uri).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception("Failed to load analysis detail");
      }

      return jsonDecode(response.body);
    } on http.ClientException {
      throw Exception("Unable to connect to backend.");
    } on TimeoutException {
      throw Exception("Detail request timed out.");
    }
  }

  // ==============================
  // AUTHENTICATION
  // ==============================
  static Future<Map<String, dynamic>> login(String username, String password) async {
    final uri = Uri.parse("$baseUrl/login");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"username": username, "password": password}),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception("Invalid username or password");
      }

      final data = jsonDecode(response.body);
      currentUserId = data['user_id'];
      currentUsername = data['username'];
      return data;
    } catch (e) {
      throw Exception("Login failed: $e");
    }
  }

  static Future<Map<String, dynamic>> register(String username, String password) async {
    final uri = Uri.parse("$baseUrl/register");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"username": username, "password": password}),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        final error = jsonDecode(response.body)['detail'] ?? "Registration failed";
        throw Exception(error);
      }

      final data = jsonDecode(response.body);
      currentUserId = data['user_id'];
      currentUsername = data['username'];
      return data;
    } catch (e) {
      throw Exception(e.toString());
    }
  }

  static void logout() {
    currentUserId = null;
    currentUsername = null;
  }

  static Future<void> deleteHistoryItem(String id) async {
    final uri = Uri.parse("$baseUrl/history/$id");

    try {
      final response =
          await http.delete(uri).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception("Failed to delete analysis record");
      }
    } on http.ClientException {
      throw Exception("Unable to connect to backend.");
    } on TimeoutException {
      throw Exception("Delete request timed out.");
    } catch (e) {
      throw Exception("Delete error: ${e.toString()}");
    }
  }
}


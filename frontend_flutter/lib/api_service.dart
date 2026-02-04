import 'dart:convert';
import 'dart:typed_data';
import 'dart:async';
import 'package:http/http.dart' as http;

class ApiService {
  // Change this if deploying
  static const String baseUrl = "http://localhost:8001";

  // ==============================
  // PDF ANALYSIS
  // ==============================
  static Future<Map<String, dynamic>> analyzePdf(
    Uint8List fileBytes,
    String fileName,
  ) async {
    final uri = Uri.parse("$baseUrl/analyze");

    var request = http.MultipartRequest("POST", uri);

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
}


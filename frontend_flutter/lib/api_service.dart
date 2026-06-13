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
  static String? currentUserRole;

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
  static Future<Map<String, dynamic>> login(String username, String password, {String role = 'client'}) async {
    final uri = Uri.parse("$baseUrl/login");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "username": username,
          "password": password,
          "role": role,
        }),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        throw Exception("Invalid username or password");
      }

      final data = jsonDecode(response.body);
      currentUserId = data['user_id'];
      currentUsername = data['username'];
      currentUserRole = data['role'] ?? 'client';
      return data;
    } catch (e) {
      throw Exception("Login failed: $e");
    }
  }

  static Future<Map<String, dynamic>> register(String username, String password, {String role = 'client'}) async {
    final uri = Uri.parse("$baseUrl/register");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"username": username, "password": password, "role": role}),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        final error = jsonDecode(response.body)['detail'] ?? "Registration failed";
        throw Exception(error);
      }

      final data = jsonDecode(response.body);
      currentUserId = data['user_id'];
      currentUsername = data['username'];
      currentUserRole = data['role'] ?? role;
      return data;
    } catch (e) {
      throw Exception(e.toString());
    }
  }

  static void logout() {
    currentUserId = null;
    currentUsername = null;
    currentUserRole = null;
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

  // ==============================
  // COMPARISON
  // ==============================
  static Future<Map<String, dynamic>> compareContracts(List<String> docIds) async {
    final uri = Uri.parse("$baseUrl/compare");

    try {
      final response = await http
          .post(
            uri,
            headers: {"Content-Type": "application/json"},
            body: jsonEncode({"doc_ids": docIds}),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode != 200) {
        throw Exception("Comparison failed: ${response.statusCode}");
      }

      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Comparison error: ${e.toString()}");
    }
  }

  // ==============================
  // NEGOTIATION ROOMS
  // ==============================
  static Future<Map<String, dynamic>> createOrJoinRoom({
    required String leaseId,
    String? name,
  }) async {
    final uri = Uri.parse("$baseUrl/negotiate/room");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "user_id": currentUserId,
          "lease_id": leaseId,
          "role": currentUserRole ?? "client",
          "name": name,
        }),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body)['detail'] ?? "Failed";
        throw Exception(err);
      }
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Room error: $e");
    }
  }

  static Future<Map<String, dynamic>> joinRoomByCode(String code) async {
    final uri = Uri.parse("$baseUrl/negotiate/join-by-code");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "user_id": currentUserId,
          "access_code": code,
          "role": currentUserRole ?? "client",
        }),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body)['detail'] ?? "Failed to join";
        throw Exception(err);
      }
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Join error: $e");
    }
  }

  static Future<List<dynamic>> getNegotiationRooms() async {
    final role = currentUserRole ?? 'client';
    final uri = Uri.parse("$baseUrl/negotiate/rooms?user_id=$currentUserId&role=$role");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception("Failed to load rooms");
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Rooms error: $e");
    }
  }

  static Future<List<dynamic>> getRoomMessages(String roomId) async {
    final uri = Uri.parse("$baseUrl/negotiate/room/$roomId/messages");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception("Failed to load messages");
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Messages error: $e");
    }
  }

  static Future<Map<String, dynamic>> getRoomContract(String roomId) async {
    final uri = Uri.parse("$baseUrl/negotiate/room/$roomId/contract");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception("Failed to load contract");
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Contract error: $e");
    }
  }

  static Future<String> getAiAdvice(String roomId, List<Map<String, dynamic>> recentMessages) async {
    final uri = Uri.parse("$baseUrl/negotiate/advice");
    try {
      final response = await http.post(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "room_id": roomId,
          "user_id": currentUserId,
          "recent_messages": recentMessages,
        }),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body)['detail'] ?? "Advice failed";
        throw Exception(err);
      }
      final data = jsonDecode(response.body);
      return data['advice'] ?? 'No advice available.';
    } catch (e) {
      throw Exception("AI Advice error: $e");
    }
  }
  static Future<List<dynamic>> getAvailableRooms() async {
    final uri = Uri.parse("$baseUrl/negotiate/available-rooms?user_id=$currentUserId");
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception("Failed to load available rooms");
      return jsonDecode(response.body);
    } catch (e) {
      throw Exception("Available rooms error: $e");
    }
  }

  static Future<void> renameRoom(String roomId, String newName) async {
    final uri = Uri.parse("$baseUrl/negotiate/room/$roomId");
    try {
      final response = await http.put(
        uri,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"name": newName, "user_id": currentUserId}),
      ).timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception("Failed to rename room");
    } catch (e) {
      throw Exception("Rename error: $e");
    }
  }

  static Future<void> deleteRoom(String roomId) async {
    final uri = Uri.parse("$baseUrl/negotiate/room/$roomId?user_id=$currentUserId");
    try {
      final response = await http.delete(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode != 200) throw Exception("Failed to delete room");
    } catch (e) {
      throw Exception("Delete error: $e");
    }
  }
}

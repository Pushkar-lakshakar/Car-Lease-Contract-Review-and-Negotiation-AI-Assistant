import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  static const String _baseWsUrl = "ws://localhost:8001";
  
  WebSocketChannel? _channel;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  bool _isConnected = false;
  
  String? roomId;
  String? userId;
  String? role;

  Stream<Map<String, dynamic>> get messages => _messageController.stream;
  bool get isConnected => _isConnected;

  void connect({
    required String roomId,
    required String userId,
    required String role,
  }) {
    // Ensure we don't have dangling connections/listeners
    if (_channel != null || _isConnected) {
      disconnect();
    }

    this.roomId = roomId;
    this.userId = userId;
    this.role = role;

    final uri = Uri.parse("$_baseWsUrl/ws/negotiate/$roomId?user_id=$userId&role=$role");
    
    try {
      _channel = WebSocketChannel.connect(uri);
      _isConnected = true;
      
      _channel!.stream.listen(
        (data) {
          try {
            final decoded = jsonDecode(data as String);
            _messageController.add(decoded);
          } catch (e) {
            print("WebSocket parse error: $e");
          }
        },
        onDone: () {
          _isConnected = false;
          print("WebSocket connection closed");
        },
        onError: (error) {
          _isConnected = false;
          print("WebSocket error: $error");
        },
      );
    } catch (e) {
      _isConnected = false;
      print("WebSocket connection failed: $e");
    }
  }

  void sendMessage(String content) {
    if (_channel != null && _isConnected) {
      _channel!.sink.add(jsonEncode({"content": content}));
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _isConnected = false;
  }

  void dispose() {
    disconnect();
    _messageController.close();
  }
}

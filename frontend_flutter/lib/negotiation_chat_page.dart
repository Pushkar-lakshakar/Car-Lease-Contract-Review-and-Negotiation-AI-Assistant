import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'api_service.dart';
import 'websocket_service.dart';
import 'theme.dart';

class NegotiationChatPage extends StatefulWidget {
  final String roomId;
  final String? leaseFilename;

  const NegotiationChatPage({
    super.key,
    required this.roomId,
    this.leaseFilename,
  });

  @override
  State<NegotiationChatPage> createState() => _NegotiationChatPageState();
}

class _NegotiationChatPageState extends State<NegotiationChatPage> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final WebSocketService _wsService = WebSocketService();
  final List<Map<String, dynamic>> _messages = [];

  bool _isLoadingHistory = true;
  bool _isLoadingAdvice = false;
  String? _aiAdvice;
  bool _showAdvicePanel = false;

  // Contract summary
  String _filename = "";
  String _fairnessScore = "N/A";
  String _riskLevel = "N/A";
  List<String> _redFlags = [];
  String? _accessCode;
  bool _showAccessCode = false;

  @override
  void initState() {
    super.initState();
    _loadContractAndHistory();
    _connectWebSocket();
  }

  Future<void> _loadContractAndHistory() async {
    try {
      // Load contract details
      final contractRes = await ApiService.getRoomContract(widget.roomId);
      final contract = contractRes['contract'] ?? {};
      final analysis = contract['analysis'] ?? contract['risk_analysis'] ?? {};

      setState(() {
        _filename = contractRes['room_name'] ?? contractRes['filename'] ?? widget.leaseFilename ?? 'Unknown';
        _fairnessScore = (analysis['contract_fairness_score'] ?? 'N/A').toString();
        _riskLevel = (analysis['risk_level'] ?? 'N/A').toString();
        _redFlags = List<String>.from(analysis['red_flags'] ?? []);
        _accessCode = contractRes['access_code'];
      });

      // Load message history
      final history = await ApiService.getRoomMessages(widget.roomId);
      setState(() {
        for (var msg in history) {
          _messages.add(Map<String, dynamic>.from(msg));
        }
        _isLoadingHistory = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _isLoadingHistory = false);
      debugPrint("Load error: $e");
    }
  }

  void _connectWebSocket() {
    _wsService.connect(
      roomId: widget.roomId,
      userId: ApiService.currentUserId ?? "",
      role: ApiService.currentUserRole ?? "client",
    );

    _wsService.messages.listen((msg) {
      if (msg['type'] == 'message') {
        // Avoid duplicates from own messages
        final exists = _messages.any((m) => m['id'] == msg['id']);
        if (!exists) {
          setState(() => _messages.add(msg));
          _scrollToBottom();
        }
      } else if (msg['type'] == 'system') {
        setState(() => _messages.add(msg));
        _scrollToBottom();
      }
    });
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    // Optimistically add to local list - REMOVED to prevent duplicates
    // waiting for WS broadcast which has the correct DB ID
    // setState(() => _messages.add(localMsg));
    // _scrollToBottom();

    _wsService.sendMessage(text);
    _messageController.clear();
  }

  Future<void> _getAiAdvice() async {
    setState(() {
      _isLoadingAdvice = true;
      _showAdvicePanel = true;
    });

    try {
      // Prepare recent messages for context
      final recent = _messages
          .where((m) => m['type'] == 'message')
          .toList()
          .reversed
          .take(50)
          .toList()
          .reversed
          .map((m) => {
                'sender_role': m['sender_role'] ?? '',
                'content': m['content'] ?? '',
              })
          .toList();

      final advice = await ApiService.getAiAdvice(widget.roomId, recent);
      setState(() {
        _aiAdvice = advice;
        _isLoadingAdvice = false;
      });
    } catch (e) {
      String errorMsg;
      final errStr = e.toString();
      if (errStr.contains('429') || errStr.contains('RESOURCE_EXHAUSTED') || errStr.contains('rate')) {
        errorMsg = "**API rate limit reached.** The free Gemini API has usage limits.\n\nPlease wait ~60 seconds and try again.";
      } else {
        errorMsg = "Failed to get advice. Please try again later.";
      }
      setState(() {
        _aiAdvice = errorMsg;
        _isLoadingAdvice = false;
      });
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _wsService.dispose();
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isClient = (ApiService.currentUserRole ?? 'client') == 'client';
    final screenWidth = MediaQuery.of(context).size.width;
    final isWide = screenWidth > 800;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_filename, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)), // Show Room Name
            if (_accessCode != null)
              GestureDetector(
                onTap: () => setState(() => _showAccessCode = !_showAccessCode),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.vpn_key, size: 12, color: Colors.white70),
                    const SizedBox(width: 4),
                    Text(
                      "Code: ${_showAccessCode ? _accessCode : '••••••'}",
                      style: const TextStyle(fontSize: 13, color: Colors.white70),
                    ),
                    const SizedBox(width: 4),
                    Icon(
                      _showAccessCode ? Icons.visibility_off : Icons.visibility,
                      size: 12,
                      color: Colors.white70,
                    ),
                  ],
                ),
              )
            else
               Text("Negotiation Chat", style: TextStyle(fontSize: 12, color: Colors.grey[400])),
          ],
        ),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
        elevation: 2,
        actions: [
          if (isClient)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: TextButton.icon(
                onPressed: _isLoadingAdvice ? null : _getAiAdvice,
                icon: const Icon(Icons.auto_awesome, color: Colors.amber, size: 20),
                label: Text(
                  _showAdvicePanel ? "Refresh Advice" : "AI Advice",
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                ),
              ),
            ),
        ],
      ),
      body: SelectionArea(
        child: isWide
            ? Row(
                children: [
                  // Main chat area
                  Expanded(flex: 3, child: _buildChatArea()),
                  // Side panels
                  if (isClient && _showAdvicePanel)
                    Expanded(flex: 2, child: _buildAdvicePanel()),
                ],
              )
            : Column(
                children: [
                  // Contract summary strip
                  _buildContractSummaryStrip(),
                  // Chat area
                  Expanded(child: _buildChatArea()),
                  // AI Advice bottom sheet (for narrow screens)
                  if (isClient && _showAdvicePanel) _buildAdvicePanelCompact(),
                ],
              ),
      ),
    );
  }

  Widget _buildContractSummaryStrip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
      ),
      child: Row(
        children: [
          _summaryChip("Score", _fairnessScore, Colors.indigo),
          const SizedBox(width: 12),
          _summaryChip("Risk", _riskLevel, _riskColor()),
          const SizedBox(width: 12),
          _summaryChip("Issues", "${_redFlags.length}", Colors.orange),
        ],
      ),
    );
  }

  Widget _summaryChip(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text("$label: ", style: TextStyle(fontSize: 11, color: Colors.grey[600])),
          Text(value, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Color _riskColor() {
    switch (_riskLevel.toUpperCase()) {
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      case 'LOW':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Widget _buildChatArea() {
    return Column(
      children: [
        // Contract summary strip (wide mode)
        if (MediaQuery.of(context).size.width > 800) _buildContractSummaryStrip(),
        // Messages
        Expanded(
          child: _isLoadingHistory
              ? const Center(child: CircularProgressIndicator())
              : _messages.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey[300]),
                          const SizedBox(height: 16),
                          Text("No messages yet.\nStart the negotiation!",
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.grey[500], fontSize: 16)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: _messages.length,
                      itemBuilder: (context, index) {
                        final msg = _messages[index];
                        if (msg['type'] == 'system') {
                          return _buildSystemMessage(msg);
                        }
                        return _buildChatBubble(msg);
                      },
                    ),
        ),
        // Input bar
        _buildInputBar(),
      ],
    );
  }

  Widget _buildSystemMessage(Map<String, dynamic> msg) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.grey[200],
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            msg['content'] ?? '',
            style: TextStyle(fontSize: 12, color: Colors.grey[600], fontStyle: FontStyle.italic),
          ),
        ),
      ),
    );
  }

  Widget _buildChatBubble(Map<String, dynamic> msg) {
    final isMe = msg['sender_id'] == ApiService.currentUserId;
    final isClient = msg['sender_role'] == 'client';
    final bubbleColor = isMe 
        ? (isClient ? const Color(0xFF4F46E5) : const Color(0xFF059669))
        : (isClient ? const Color(0xFFE8E5FF) : const Color(0xFFD1FAE5));
    final textColor = isMe ? Colors.white : Colors.black87;
    final roleLabel = isClient ? "Client" : "Dealer";
    final username = msg['username'] ?? roleLabel;

    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.7),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isMe ? const Radius.circular(16) : const Radius.circular(4),
            bottomRight: isMe ? const Radius.circular(4) : const Radius.circular(16),
          ),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 2)),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: isMe ? Colors.white.withOpacity(0.2) : Colors.black.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      "$username • $roleLabel",
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: textColor.withOpacity(0.8)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(msg['content'] ?? '', style: TextStyle(color: textColor, fontSize: 14)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey[200]!)),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 8, offset: const Offset(0, -2)),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                decoration: InputDecoration(
                  hintText: "Type your message...",
                  hintStyle: TextStyle(color: Colors.grey[400]),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(color: Colors.grey[300]!),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  filled: true,
                  fillColor: Colors.grey[50],
                ),
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppTheme.primaryColor, AppTheme.secondaryColor],
                ),
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: const Icon(Icons.send_rounded, color: Colors.white),
                onPressed: _sendMessage,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // AI Advice panel (side panel for wide screens)
  Widget _buildAdvicePanel() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7ED),
        border: Border(left: BorderSide(color: Colors.amber[200]!, width: 2)),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.amber[100]!, Colors.orange[50]!],
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.auto_awesome, color: Colors.amber, size: 24),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text("AI Negotiation Advisor",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: () => setState(() => _showAdvicePanel = false),
                ),
              ],
            ),
          ),
          // Content
          Expanded(
            child: _isLoadingAdvice
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(color: Colors.amber),
                        SizedBox(height: 12),
                        Text("Analyzing conversation..."),
                      ],
                    ),
                  )
                : _aiAdvice != null
                    ? SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: MarkdownBody(data: _aiAdvice!),
                      )
                    : const Center(child: Text("Click 'AI Advice' to get tips")),
          ),
          // Refresh button
          Padding(
            padding: const EdgeInsets.all(12),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isLoadingAdvice ? null : _getAiAdvice,
                icon: const Icon(Icons.refresh),
                label: const Text("Refresh Advice"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.amber[700],
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // Compact advice panel for narrow screens
  Widget _buildAdvicePanelCompact() {
    return Container(
      constraints: const BoxConstraints(maxHeight: 200),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7ED),
        border: Border(top: BorderSide(color: Colors.amber[300]!, width: 2)),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            color: Colors.amber[50],
            child: Row(
              children: [
                const Icon(Icons.auto_awesome, color: Colors.amber, size: 18),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text("AI Advisor", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 16),
                  onPressed: () => setState(() => _showAdvicePanel = false),
                  constraints: const BoxConstraints(),
                  padding: EdgeInsets.zero,
                ),
              ],
            ),
          ),
          Expanded(
            child: _isLoadingAdvice
                ? const Center(child: CircularProgressIndicator(color: Colors.amber))
                : _aiAdvice != null
                    ? SingleChildScrollView(
                        padding: const EdgeInsets.all(12),
                        child: MarkdownBody(data: _aiAdvice!),
                      )
                    : const Center(child: Text("Tap AI Advice to get tips", style: TextStyle(fontSize: 12))),
          ),
        ],
      ),
    );
  }
}

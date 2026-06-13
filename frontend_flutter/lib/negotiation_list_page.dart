import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'api_service.dart';
import 'negotiation_chat_page.dart';

class NegotiationListPage extends StatefulWidget {
  const NegotiationListPage({super.key});

  @override
  State<NegotiationListPage> createState() => _NegotiationListPageState();
}

class _NegotiationListPageState extends State<NegotiationListPage> {
  List<dynamic> _myRooms = [];
  bool _isLoading = true;
  Map<String, bool> _revealedCodes = {};

  @override
  void initState() {
    super.initState();
    _loadMyRooms();
  }

  Future<void> _loadMyRooms() async {
    setState(() => _isLoading = true);
    try {
      final rooms = await ApiService.getNegotiationRooms();
      if (mounted) {
        setState(() {
          _myRooms = rooms;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Error loading rooms: $e")));
      }
    }
  }

  Future<void> _renameRoom(String roomId, String currentName) async {
    final TextEditingController _nameController = TextEditingController(text: currentName);
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Rename Negotiation"),
        content: TextField(
          controller: _nameController,
          decoration: const InputDecoration(labelText: "Name"),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () async {
              final newName = _nameController.text.trim();
              if (newName.isNotEmpty) {
                Navigator.pop(context);
                try {
                  await ApiService.renameRoom(roomId, newName);
                  _loadMyRooms();
                } catch (e) {
                  if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                }
              }
            },
            child: const Text("Save"),
          ),
        ],
      ),
    );
  }

  Future<void> _deleteRoom(String roomId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Delete Negotiation"),
        content: const Text("Are you sure? This will delete all chat history permanently."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("Cancel")),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text("Delete", style: TextStyle(color: Colors.red))),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await ApiService.deleteRoom(roomId);
        _loadMyRooms();
      } catch (e) {
        if(mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Negotiation Spaces"),
        backgroundColor: Colors.indigo.shade600,
        foregroundColor: Colors.white,
      ),
      body: Container(
        color: const Color(0xFFF8FAFC),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _myRooms.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey.shade300),
                        const SizedBox(height: 16),
                        Text(
                          "No active negotiations",
                          style: TextStyle(fontSize: 18, color: Colors.grey.shade500),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _myRooms.length,
                    itemBuilder: (context, index) {
                      final room = _myRooms[index];
                      final roomId = room['room_id'];
                      final filename = room['filename'] ?? "Contract";
                      final name = room['name'] ?? filename;
                      final accessCode = room['access_code'];
                      final isRevealed = _revealedCodes[roomId] ?? false;

                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.indigo.shade50),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.indigo.shade100.withOpacity(0.1),
                              blurRadius: 8,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Column(
                          children: [
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: Colors.indigo.shade50,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Icon(Icons.description, color: Colors.indigo.shade400),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: GestureDetector(
                                    behavior: HitTestBehavior.opaque,
                                    onTap: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) => NegotiationChatPage(
                                            roomId: roomId,
                                            leaseFilename: filename,
                                          ),
                                        ),
                                      ).then((_) => _loadMyRooms());
                                    },
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          name,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1E293B)),
                                        ),
                                        if (name != filename)
                                          Text(
                                            filename,
                                            style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                                          ),
                                        const SizedBox(height: 4),
                                        if (accessCode != null)
                                          Row(
                                            children: [
                                              Text(
                                                "Code: ",
                                                style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                                              ),
                                              Text(
                                                isRevealed ? accessCode : "••••••",
                                                style: TextStyle(
                                                  fontSize: 14, 
                                                  fontWeight: FontWeight.bold, 
                                                  color: isRevealed ? Colors.green.shade700 : Colors.grey.shade500,
                                                  letterSpacing: isRevealed ? 2 : 0,
                                                ),
                                              ),
                                              const SizedBox(width: 8),
                                              GestureDetector(
                                                onTap: () {
                                                  setState(() {
                                                    _revealedCodes[roomId] = !isRevealed;
                                                  });
                                                },
                                                child: Icon(
                                                  isRevealed ? Icons.visibility_off : Icons.visibility,
                                                  size: 18,
                                                  color: Colors.indigo.shade300,
                                                ),
                                              ),
                                            ],
                                          ),
                                      ],
                                    ),
                                  ),
                                ),
                                PopupMenuButton<String>(
                                  icon: const Icon(Icons.more_vert, color: Colors.grey),
                                  onSelected: (value) {
                                    if (value == 'chat') {
                                       Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) => NegotiationChatPage(
                                            roomId: roomId,
                                            leaseFilename: filename,
                                          ),
                                        ),
                                      ).then((_) => _loadMyRooms());
                                    } else if (value == 'rename') {
                                      _renameRoom(roomId, name);
                                    } else if (value == 'delete') {
                                      _deleteRoom(roomId);
                                    }
                                  },
                                  itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                                    const PopupMenuItem<String>(
                                      value: 'chat',
                                      child: ListTile(
                                        leading: Icon(Icons.chat_bubble_outline),
                                        title: Text('Chat'),
                                        contentPadding: EdgeInsets.zero,
                                      ),
                                    ),
                                     const PopupMenuItem<String>(
                                      value: 'rename',
                                      child: ListTile(
                                        leading: Icon(Icons.edit),
                                        title: Text('Rename'),
                                        contentPadding: EdgeInsets.zero,
                                      ),
                                    ),
                                     const PopupMenuItem<String>(
                                      value: 'delete',
                                      child: ListTile(
                                        leading: Icon(Icons.delete, color: Colors.red),
                                        title: Text('Delete', style: TextStyle(color: Colors.red)),
                                        contentPadding: EdgeInsets.zero,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}

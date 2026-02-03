import 'package:flutter/material.dart';
import 'api_service.dart';
import 'package:file_picker/file_picker.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  Map<String, dynamic>? analysisResult;
  bool isLoading = false;

  // ✅ CHAT STATE
  List<Map<String, dynamic>> chatMessages = [];
  final TextEditingController _chatController = TextEditingController();
  bool isChatLoading = false;

  Future<void> _uploadFile() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: true,
    );

    if (picked == null || picked.files.single.bytes == null) return;

    setState(() => isLoading = true);

    try {
      final response = await ApiService.analyzePdf(
        picked.files.single.bytes!,
        picked.files.single.name,
      );

      setState(() {
        analysisResult = response;
        isLoading = false;
        chatMessages.clear(); // reset chat on new contract
      });
    } catch (e) {
      setState(() => isLoading = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  // ✅ CHAT SEND FUNCTION
  Future<void> _sendChatMessage() async {
    final message = _chatController.text.trim();
    if (message.isEmpty) return;

    setState(() {
      chatMessages.add({"text": message, "isUser": true});
      isChatLoading = true;
    });

    _chatController.clear();

    try {
      final reply = await ApiService.sendChatMessage(
        message,
        analysisResult, // send full contract JSON as context
      );

      setState(() {
        chatMessages.add({"text": reply, "isUser": false});
        isChatLoading = false;
      });
    } catch (e) {
      setState(() => isChatLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F9),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1200),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(flex: 3, child: _buildMainContent()),
                const SizedBox(width: 16),
                SizedBox(width: 320, child: _buildAssistantPanel()),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMainContent() {
    return ListView(
      children: [
        _buildHeaderCard(),
        const SizedBox(height: 16),
        _buildUploadCard(),
        const SizedBox(height: 16),
        if (analysisResult != null && !isLoading) _buildResults(),
      ],
    );
  }

  Widget _buildHeaderCard() {
    return _sectionContainer(
      const Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.directions_car, size: 32, color: Colors.blue),
            SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Car Contract Analyzer",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 4),
                Text("Upload lease PDF to analyze"),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildUploadCard() {
    return _sectionContainer(
      Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            if (isLoading)
              const Column(
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 12),
                  Text("Analyzing..."),
                ],
              )
            else
              Column(
                children: [
                  const Icon(Icons.picture_as_pdf, size: 48),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: _uploadFile,
                    child: const Text("Upload Contract"),
                  ),
                ],
              )
          ],
        ),
      ),
    );
  }

  Widget _buildResults() {
    final sla = analysisResult!["sla_fields"];
    final verification = analysisResult!["vehicle_verification"];
    final risk = analysisResult!["risk_analysis"];
    final issues = analysisResult!["issues"];
    final recommendations = analysisResult!["recommendations"];

    final financial = sla["financial"] ?? {};
    final usage = sla["usage"] ?? {};
    final insurance = sla["insurance_maintenance"] ?? {};

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionTitle("Vehicle Details in Contract"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: _infoGrid([
              _infoTile("Lessor", sla["parties"]["lessor_name"]),
              _infoTile("Lessee", sla["parties"]["lessee_name"]),
              _infoTile("Lessor Address", sla["parties"]["lessor_address"]),
              _infoTile("Lessee Address", sla["parties"]["lessee_address"]),
            ]),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Vehicle Information"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: _infoGrid([
              _infoTile("Make", sla["vehicle"]["make"]),
              _infoTile("Model", sla["vehicle"]["model"]),
              _infoTile("Year", sla["vehicle"]["year"]),
              _infoTile("VIN", sla["vehicle"]["vin"]),
              _infoTile("Fuel", verification["api_values"]["fuel_type"]),
              _infoTile("HP", verification["api_values"]["horsepower"]),
            ]),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Vehicle Verification"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              children: [
                _infoGrid([
                  _infoTile("VIN Verified", verification["verified"]),
                  _infoTile("Blacklist Status",
                      verification["blacklist_status"]["overall_status"]),
                  _infoTile("Details Available",
                      verification["full_details_available"]),
                ]),
                const SizedBox(height: 12),
                _infoGrid([
                  _infoTile("VIN", verification["key_specs"]["vin"]),
                  _infoTile("Make", verification["key_specs"]["make"]),
                  _infoTile("Model", verification["key_specs"]["model"]),
                  _infoTile("Year", verification["key_specs"]["year"]),
                  _infoTile("Vehicle Type",
                      verification["key_specs"]["vehicle_type"]),
                  _infoTile("Fuel Type",
                      verification["key_specs"]["fuel_type"]),
                  _infoTile("Engine Size",
                      verification["key_specs"]["engine_size"]),
                  _infoTile("Horsepower",
                      verification["key_specs"]["horsepower"]),
                ]),
              ],
            ),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Analysis"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                    child:
                        _flagCard("Red Flags", issues["red_flags"], Colors.red)),
                const SizedBox(width: 12),
                Expanded(
                    child: _flagCard(
                        "Recommendations", recommendations, Colors.green)),
              ],
            ),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Health Score"),
        _healthScoreCard(risk),
      ],
    );
  }

  Widget _sectionContainer(Widget child) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: child,
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(title,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
    );
  }

  Widget _infoGrid(List<Widget> children) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        mainAxisExtent: 70,
      ),
      itemCount: children.length,
      itemBuilder: (context, index) => children[index],
    );
  }

  Widget _infoTile(String label, dynamic value) {
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border(
          left: BorderSide(color: Colors.blue.shade400, width: 3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
          const SizedBox(height: 4),
          Text(value?.toString() ?? "Not Found",
              style:
                  const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _flagCard(String title, List<dynamic> items, Color color) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style:
                  TextStyle(fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 8),
          ...items.map(
            (e) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text("• ${e.toString()}",
                  style: const TextStyle(fontSize: 12)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _healthScoreCard(Map<String, dynamic> risk) {
    final score = risk["contract_fairness_score"] ?? 0;
    final level = risk["contract_fairness_level"] ?? "UNKNOWN";

    return _sectionContainer(
      Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          children: [
            Text("$score%",
                style:
                    const TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(level, style: const TextStyle(fontSize: 13)),
          ],
        ),
      ),
    );
  }

  // ✅ CHAT UI
  Widget _buildAssistantPanel() {
    return Container(
      height: 600,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        children: [
          const Text(
            "Lease Analysis Assistant",
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: ListView(
              children: chatMessages.map((msg) {
                final isUser = msg["isUser"];
                return Align(
                  alignment: isUser
                      ? Alignment.centerRight
                      : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: isUser
                          ? Colors.blue
                          : const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      msg["text"],
                      style: TextStyle(
                        color: isUser ? Colors.white : Colors.black,
                        fontSize: 12,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          if (isChatLoading)
            const Padding(
              padding: EdgeInsets.all(8),
              child: CircularProgressIndicator(),
            ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _chatController,
                  decoration: const InputDecoration(
                    hintText: "Ask about this contract...",
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.send),
                onPressed: _sendChatMessage,
              )
            ],
          )
        ],
      ),
    );
  }
}

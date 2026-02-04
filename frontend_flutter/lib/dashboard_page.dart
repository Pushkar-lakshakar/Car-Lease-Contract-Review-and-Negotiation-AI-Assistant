import 'package:flutter/material.dart';
import 'api_service.dart';
import 'chatbot_service.dart';
import 'package:file_picker/file_picker.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  Map<String, dynamic>? analysisResult;
  bool isLoading = false;

  // ✅ CHAT SERVICE
  final ChatbotService _chatService = ChatbotService();

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
        // Feed contract data to chatbot for context
        _chatService.setContractContext(response);
      });
    } catch (e) {
      setState(() => isLoading = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  // ✅ CHAT SEND FUNCTION
  final TextEditingController _chatController = TextEditingController();

  Future<void> _sendChatMessage() async {
    final message = _chatController.text.trim();
    if (message.isEmpty) return;

    _chatController.clear();
    setState(() {}); // Trigger rebuild to show user message

    try {
      await _chatService.sendMessage(message);
      setState(() {}); // Trigger rebuild to show AI response
    } catch (e) {
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFEEF2FF), Color(0xFFF8FAFC), Color(0xFFE0E7FF)],
          ),
        ),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1400),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(flex: 3, child: _buildMainContent()),
                  const SizedBox(width: 24),
                  SizedBox(width: 380, child: _buildAssistantPanel()),
                ],
              ),
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
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF4F46E5).withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(Icons.auto_awesome_motion,
                size: 40, color: Colors.white),
          ),
          const SizedBox(width: 20),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Car Lease Analyzer Pro",
                style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: -0.5),
              ),
              SizedBox(height: 6),
              Text(
                "AI-Powered Contract Intelligence & Verification",
                style: TextStyle(
                    color: Colors.white70,
                    fontSize: 15,
                    fontWeight: FontWeight.w500),
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildUploadCard() {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.indigo.shade50, width: 2),
        boxShadow: [
          BoxShadow(
              color: Colors.indigo.shade100.withOpacity(0.1),
              blurRadius: 15,
              offset: const Offset(0, 8))
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isLoading ? null : _uploadFile,
          borderRadius: BorderRadius.circular(24),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 40),
            child: Column(
              children: [
                if (isLoading)
                  Column(
                    children: [
                      const SizedBox(
                          width: 40,
                          height: 40,
                          child: CircularProgressIndicator(strokeWidth: 3)),
                      const SizedBox(height: 20),
                      Text("Analyzing Contract...",
                          style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.indigo.shade900)),
                      const SizedBox(height: 8),
                      Text("Extracting terms, verifying vehicle, and detecting risks",
                          style: TextStyle(color: Colors.indigo.shade400)),
                    ],
                  )
                else
                  Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.indigo.shade50,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(Icons.cloud_upload_rounded,
                            size: 48, color: Colors.indigo.shade500),
                      ),
                      const SizedBox(height: 16),
                      Text("Click to Upload Contract",
                          style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.indigo.shade900)),
                      const SizedBox(height: 8),
                      Text("Supports PDF files up to 20MB",
                          style: TextStyle(color: Colors.indigo.shade300)),
                    ],
                  ),
              ],
            ),
          ),
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

        _sectionTitle("Financial Terms"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: _infoGrid([
              _infoTile("Monthly Rental", financial["monthly_rental"]),
              _infoTile("Security Deposit", financial["security_deposit"]),
              _infoTile("Lease Term", financial["lease_term"]),
              _infoTile("Start Date", financial["start_date"]),
              _infoTile("End Date", financial["end_date"]),
              _infoTile("Payment Due", financial["payment_due_day"]),
            ]),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Mileage & Usage"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: _infoGrid([
              _infoTile("Annual Limit", usage["annual_mileage"]),
              _infoTile("Total Allowed", usage["total_mileage"]),
              _infoTile("Excess Charge", usage["excess_charge"]),
              _infoTile("Usage Type", usage["permitted_use"]),
            ]),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Insurance & Maintenance"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(8),
            child: _infoGrid([
              _infoTile("Insurance Req", insurance["insurance_requirements"]),
              _infoTile("Ins. Provider", insurance["insurance_provider"]),
              _infoTile("Maintenance By", insurance["maintenance_responsibility"]),
              _infoTile("Routine Maint.", insurance["routine_maintenance_included"]),
            ]),
          ),
        ),

        const SizedBox(height: 16),

        _sectionTitle("Analysis & Recommendations"),
        _sectionContainer(
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _flagCard("Red Flags", issues["red_flags"], Colors.red, Icons.report_problem_rounded),
                if (issues["vehicle_mismatches"] != null && (issues["vehicle_mismatches"] as List).isNotEmpty) ...[
                  const SizedBox(height: 12),
                  _flagCard("Vehicle Mismatches", issues["vehicle_mismatches"], Colors.orange, Icons.minor_crash_rounded),
                ],
                const SizedBox(height: 12),
                _flagCard("Key Recommendations", recommendations, Colors.teal, Icons.lightbulb_rounded),
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
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.indigo.shade50),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.shade100.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: child,
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12, left: 4),
      child: Row(
        children: [
          Container(
            height: 24,
            width: 4,
            decoration: BoxDecoration(
              color: const Color(0xFF6366F1),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 8),
          Text(title,
              style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E1B4B))), // Indigo 900
        ],
      ),
    );
  }

  Widget _infoGrid(List<Widget?> children) {
    final visibleChildren = children.whereType<Widget>().toList();
    if (visibleChildren.isEmpty) return const SizedBox.shrink();

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        mainAxisExtent: 100, // Increased to 100 to prevent overflow on long text
      ),
      itemCount: visibleChildren.length,
      itemBuilder: (context, index) => visibleChildren[index],
    );
  }

  Widget? _infoTile(String label, dynamic value) {
    String valStr = value?.toString().trim() ?? "";
    if (valStr.isEmpty ||
        valStr.toLowerCase() == "not found" ||
        valStr.toLowerCase() == "not specified" ||
        valStr.toLowerCase() == "null") {
      return null;
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.indigo.shade50),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: Colors.indigo.shade400)),
          const SizedBox(height: 4),
          Text(valStr,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                  color: Colors.blueGrey.shade800)),
        ],
      ),
    );
  }

  Widget _flagCard(String title, List<dynamic> items, Color color, IconData icon) {
    if (items.isEmpty) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Text(title,
                  style: TextStyle(
                      fontWeight: FontWeight.bold, color: color, fontSize: 15)),
            ],
          ),
          const SizedBox(height: 12),
          ...items.map(
            (e) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Icon(Icons.circle, size: 6, color: color.withOpacity(0.5)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(e.toString(),
                        style: TextStyle(
                            fontSize: 13, 
                            color: Colors.blueGrey.shade800,
                            height: 1.4)),
                  ),
                ],
              ),
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
        padding: const EdgeInsets.all(24),
        child: Row(
          children: [
            SizedBox(
              height: 100,
              width: 100,
              child: Stack(
                children: [
                  Center(
                    child: SizedBox(
                      width: 100,
                      height: 100,
                      child: CircularProgressIndicator(
                        value: score / 100,
                        strokeWidth: 10,
                        backgroundColor: Colors.indigo.shade50,
                        color: _getScoreColor(score),
                        strokeCap: StrokeCap.round,
                      ),
                    ),
                  ),
                  Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text("$score",
                            style: const TextStyle(
                                fontSize: 24, fontWeight: FontWeight.bold)),
                        const Text("Score", style: TextStyle(fontSize: 10, color: Colors.grey)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 24),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Contract Health: $level",
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text(
                    _getScoreDescription(score),
                    style: TextStyle(color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 80) return const Color(0xFF10B981); // Emerald
    if (score >= 60) return const Color(0xFFF59E0B); // Amber
    return const Color(0xFFEF4444); // Red
  }

  String _getScoreDescription(int score) {
    if (score >= 80) return "Excellent contract terms with low risk.";
    if (score >= 60) return "Average contract with some points to review.";
    return "High risk contract with multiple red flags.";
  }

  // ✅ CHAT UI
  Widget _buildAssistantPanel() {
    return Container(
      height: 700,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.indigo.shade50),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.shade100.withOpacity(0.1),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          // Chat Header
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF4F46E5), Color(0xFF6366F1)],
              ),
              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      shape: BoxShape.circle),
                  child: const Icon(Icons.psychology, color: Colors.white),
                ),
                const SizedBox(width: 12),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("AI Assistant",
                        style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 16)),
                    Text("Ask about your contract",
                        style: TextStyle(
                            color: Colors.white70,
                            fontSize: 12)),
                  ],
                ),
              ],
            ),
          ),
          
          // Chat Messages
          Expanded(
            child: Container(
              color: const Color(0xFFF8FAFC),
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _chatService.messages.length + (_chatService.isLoading ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index == _chatService.messages.length) {
                    return Align(
                      alignment: Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: Colors.indigo.shade50),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            SizedBox(
                              width: 16, 
                              height: 16, 
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.indigo.shade300)
                            ),
                            const SizedBox(width: 8),
                            Text("Thinking...", style: TextStyle(color: Colors.indigo.shade300, fontSize: 12)),
                          ],
                        ),
                      ),
                    );
                  }
                  
                  final msg = _chatService.messages[index];
                  final isUser = msg.isUser;
                  return Align(
                    alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      constraints: const BoxConstraints(maxWidth: 260),
                      margin: const EdgeInsets.symmetric(vertical: 6),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: isUser ? const Color(0xFF4F46E5) : Colors.white,
                        borderRadius: BorderRadius.only(
                          topLeft: const Radius.circular(16),
                          topRight: const Radius.circular(16),
                          bottomLeft: Radius.circular(isUser ? 16 : 4),
                          bottomRight: Radius.circular(isUser ? 4 : 16),
                        ),
                        boxShadow: [
                          if (!isUser)
                            BoxShadow(
                                color: Colors.indigo.shade100.withOpacity(0.1),
                                blurRadius: 4,
                                offset: const Offset(0, 2))
                        ],
                      ),
                      child: Text(
                        msg.text,
                        style: TextStyle(
                          color: isUser ? Colors.white : Colors.indigo.shade900,
                          fontSize: 14,
                          height: 1.4,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),

          // Input Area
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _chatController,
                    onSubmitted: (_) => _sendChatMessage(),
                    decoration: InputDecoration(
                      hintText: "Type a question...",
                      hintStyle: TextStyle(color: Colors.grey.shade400),
                      filled: true,
                      fillColor: const Color(0xFFF1F5F9),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(30),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Color(0xFF4F46E5),
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.send_rounded, size: 20),
                    color: Colors.white,
                    onPressed: _sendChatMessage,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


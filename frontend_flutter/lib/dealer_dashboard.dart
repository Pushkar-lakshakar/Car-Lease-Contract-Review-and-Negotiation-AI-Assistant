import 'package:flutter/material.dart';
import 'api_service.dart';
import 'login_page.dart';
import 'negotiation_chat_page.dart';
import 'package:file_picker/file_picker.dart';

class DealerDashboard extends StatefulWidget {
  const DealerDashboard({super.key});

  @override
  State<DealerDashboard> createState() => _DealerDashboardState();
}

class _DealerDashboardState extends State<DealerDashboard> {
  List<dynamic> _rooms = [];
  bool _isLoadingRooms = true;
  bool _isUploading = false;
  String? _error;
  Map<String, dynamic>? _analysisResult;

  @override
  void initState() {
    super.initState();
    _loadRooms();
  }

  Future<void> _loadRooms() async {
    setState(() {
      _isLoadingRooms = true;
      _error = null;
    });

    try {
      final rooms = await ApiService.getNegotiationRooms();
      setState(() {
        _rooms = rooms;
        _isLoadingRooms = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoadingRooms = false;
        });
      }
    }
  }

  Future<void> _uploadContract() async {
    // Dealers can upload contracts to analyze them, though primary flow is usually Client uploading.
    // This allows Dealer to initiate a flow if needed.
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: true,
    );

    if (picked == null || picked.files.single.bytes == null) return;

    setState(() => _isUploading = true);

    try {
      final response = await ApiService.analyzePdf(
        picked.files.single.bytes!,
        picked.files.single.name,
      );
      
      if (!mounted) return;
      
      setState(() {
        _isUploading = false;
        _analysisResult = response;
      });

    } catch (e) {
      if (mounted) {
        setState(() => _isUploading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Widget _buildAnalysisResultsInline() {
    final sla = _analysisResult!['sla_fields'] ?? {};
    final financial = sla['financial'] ?? {};
    final vehicle = sla['vehicle'] ?? {};
    final usage = sla['usage'] ?? {};
    final insurance = sla['insurance_maintenance'] ?? {};

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF059669).withOpacity(0.2)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "Contract Terms Extraction",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF064E3B)),
              ),
              IconButton(
                onPressed: () => setState(() => _analysisResult = null),
                icon: const Icon(Icons.close, size: 20, color: Colors.grey),
                tooltip: "Clear results",
              ),
            ],
          ),
          const Divider(),
          const SizedBox(height: 8),
          _buildSectionTitle("Financial Details"),
          _buildInfoRow("Monthly Payment", financial['monthly_rental']),
          _buildInfoRow("Down Payment", financial['security_deposit']),
          _buildInfoRow("Lease Term", financial['lease_term']),
          _buildInfoRow("Start Date", financial['start_date']),
          _buildInfoRow("End Date", financial['end_date']),
          _buildInfoRow("Due Date", financial['payment_due_day']),
          
          const SizedBox(height: 16),
          _buildSectionTitle("Vehicle Information"),
          _buildInfoRow("Make", vehicle['make']),
          _buildInfoRow("Model", vehicle['model']),
          _buildInfoRow("Year", vehicle['year']),
          _buildInfoRow("VIN", vehicle['vin']),

          const SizedBox(height: 16),
          _buildSectionTitle("Usage Limits"),
          _buildInfoRow("Annual Mileage", usage['annual_mileage']),
          _buildInfoRow("Total Allowed Mileage", usage['total_mileage']),
          _buildInfoRow("Excess Charge", usage['excess_charge']),
          _buildInfoRow("Permitted Use", usage['permitted_use']),

          const SizedBox(height: 16),
          _buildSectionTitle("Insurance & Maintenance"),
          _buildInfoRow("Insurance Requirements", insurance['insurance_requirements']),
          _buildInfoRow("Maintenance Responsibility", insurance['maintenance_responsibility']),
          _buildInfoRow("Routine Maintenance Included", insurance['routine_maintenance_included']),
        ],
      ),
    );
  }

  // Keep _showAnalysisDialog for backwards compatibility or remove if not needed.
  // We'll keep it for now but call the inline version.

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF064E3B)),
      ),
    );
  }

  Widget _buildInfoRow(String label, dynamic value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600])),
          Text(
            value?.toString() ?? "N/A",
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Future<void> _joinRoom(String roomId, String? filename) async {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => NegotiationChatPage(
          roomId: roomId,
          leaseFilename: filename ?? "Contract",
        ),
      ),
    ).then((_) => _loadRooms()); // Refresh on return
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0FDF4), // Light Green bg
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(),
              const SizedBox(height: 32),
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildActionSection(),
                      const SizedBox(height: 24),
                      if (_analysisResult != null) ...[
                        _buildAnalysisResultsInline(),
                        const SizedBox(height: 24),
                      ],
                      const Text(
                        "Active Negotiations",
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF064E3B)),
                      ),
                      const SizedBox(height: 16),
                      // Since we are inside a scrollview, we give this a fixed height or use shrinkWrap
                      _buildRoomsListConstrained(),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRoomsListConstrained() {
    // We can use a fixed height or a flexible one based on screen
    return Container(
      constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.6),
      child: _buildRoomsList(),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF059669),
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF059669).withOpacity(0.3),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: const Icon(Icons.store_rounded, size: 32, color: Colors.white),
        ),
        const SizedBox(width: 16),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Dealer Dashboard",
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF064E3B)),
            ),
            Text(
              "Welcome, ${ApiService.currentUsername ?? 'Dealer'}",
              style: TextStyle(fontSize: 14, color: Colors.green[800]),
            ),
          ],
        ),
        const Spacer(),
        IconButton(
          onPressed: () {
            ApiService.logout();
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (context) => const LoginPage()),
              (route) => false,
            );
          },
          icon: const Icon(Icons.logout, color: Colors.red),
          tooltip: "Logout",
        ),
      ],
    );
  }

  Widget _buildActionSection() {
    return Row(
      children: [
        // Upload Contract (Analysis Only)
        Expanded(
          child: InkWell(
            onTap: _isUploading ? null : _uploadContract,
            borderRadius: BorderRadius.circular(16),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF059669).withOpacity(0.3), width: 1.5),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.withOpacity(0.1),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: _isUploading 
                  ? [
                      const SizedBox(
                        height: 32,
                        width: 32,
                        child: CircularProgressIndicator(color: Color(0xFF059669), strokeWidth: 3),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        "Analyzing...",
                        style: TextStyle(color: Color(0xFF064E3B), fontSize: 16, fontWeight: FontWeight.bold),
                        textAlign: TextAlign.center,
                      ),
                    ]
                  : [
                      const Icon(Icons.upload_file, color: Color(0xFF059669), size: 32),
                      const SizedBox(height: 12),
                      const Text(
                        "Analyze Contract",
                        style: TextStyle(color: Color(0xFF064E3B), fontSize: 16, fontWeight: FontWeight.bold),
                        textAlign: TextAlign.center,
                      ),
                    ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 16),
        // Join (Browse Layout)
        Expanded(
          child: InkWell(
            onTap: _showAvailableRoomsDialog,
            borderRadius: BorderRadius.circular(16),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF059669), width: 1.5),
                boxShadow: [
                  BoxShadow(
                    color: Colors.grey.withOpacity(0.1),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.list_alt_rounded, color: Color(0xFF059669), size: 32),
                  SizedBox(height: 12),
                  Text(
                    "Browse & Join",
                    style: TextStyle(color: Color(0xFF064E3B), fontSize: 16, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _showAvailableRoomsDialog() async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    
    try {
      final rooms = await ApiService.getAvailableRooms();
      if (!mounted) return;
      Navigator.pop(context); // Close loader

      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("Active Negotiations"),
          content: SizedBox(
            width: double.maxFinite,
            child: rooms.isEmpty
                ? const Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Text("No active negotiation rooms found."),
                  )
                : ListView.separated(
                    shrinkWrap: true,
                    itemCount: rooms.length,
                    separatorBuilder: (_, __) => const Divider(),
                    itemBuilder: (context, index) {
                        final room = rooms[index];
                        final isTaken = room['is_taken'] ?? false;
                        return ListTile(
                            title: Text(
                              room['name'] ?? room['filename'] ?? "Unknown",
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Text("Created: ${room['created_at']?.split('T')[0] ?? 'N/A'}"),
                            trailing: isTaken
                                ? Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: Colors.orange.shade100,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: const Text("In Use", style: TextStyle(color: Colors.orange)),
                                  )
                                : const Icon(Icons.arrow_forward_ios, size: 16),
                            onTap: () {
                                Navigator.pop(context); // Close list
                                _showJoinCodeDialog(); // Access Code is still required!
                            },
                        );
                    },
                  ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Close"),
            ),
            TextButton(
               onPressed: () {
                 Navigator.pop(context);
                 _showJoinCodeDialog(); // Manual entry
               },
               child: const Text("Enter Code Manually"),
            )
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context); // Close loader
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  void _showJoinCodeDialog() {
    final TextEditingController _codeController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Join Negotiation"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text("Enter the 6-digit access code provided by the maker:"),
            const SizedBox(height: 16),
            TextField(
              controller: _codeController,
              keyboardType: TextInputType.number,
              maxLength: 6,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: "Access Code",
                hintText: "123456",
                counterText: "",
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              final code = _codeController.text.trim();
              if (code.length != 6) return;
              
              Navigator.pop(context); // Close dialog
              
              setState(() => _isLoadingRooms = true); // Show loading
              try {
                final result = await ApiService.joinRoomByCode(code);
                if (mounted) {
                   ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("Joined successfully!")),
                  );
                  _joinRoom(result['room_id'], "Negotiation");
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("Error: ${e.toString().replaceFirst('Exception: ', '')}")),
                  );
                }
              } finally {
                if (mounted) _loadRooms();
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF059669)),
            child: const Text("Join"),
          ),
        ],
      ),
    );
  }

  Widget _buildRoomsList() {
    if (_isLoadingRooms) {
      return const Center(child: CircularProgressIndicator());
    }
    
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text("Error: $_error", style: const TextStyle(color: Colors.red)),
            TextButton(onPressed: _loadRooms, child: const Text("Retry"))
          ],
        ),
      );
    }
    
    if (_rooms.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox_outlined, size: 64, color: Colors.green[200]),
            const SizedBox(height: 16),
            Text(
              "No active negotiations",
              style: TextStyle(fontSize: 16, color: Colors.green[800]),
            ),
            Text(
              "Wait for clients to start a chat",
              style: TextStyle(fontSize: 14, color: Colors.green[600]),
            ),
            const SizedBox(height: 16),
            TextButton.icon(
              onPressed: _loadRooms,
              icon: const Icon(Icons.refresh),
              label: const Text("Refresh"),
            )
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadRooms,
      child: ListView.builder(
        itemCount: _rooms.length,
        itemBuilder: (context, index) {
          final room = _rooms[index];
          final filename = room['filename'] ?? "Unknown Contract";
          final clientName = "Client"; // We don't have client name in this endpoint yet, but that's fine
          final time = room['created_at'] != null 
              ? room['created_at'].toString().substring(0, 10) 
              : "Recently";

          return Card(
            elevation: 2,
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: ListTile(
              contentPadding: const EdgeInsets.all(16),
              leading: CircleAvatar(
                backgroundColor: const Color(0xFFECFDF5),
                child: const Icon(Icons.person, color: Color(0xFF059669)),
              ),
              title: Text(filename, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text("Started: $time"),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.grey),
              onTap: () => _joinRoom(room['room_id'], filename),
            ),
          );
        },
      ),
    );
  }
}

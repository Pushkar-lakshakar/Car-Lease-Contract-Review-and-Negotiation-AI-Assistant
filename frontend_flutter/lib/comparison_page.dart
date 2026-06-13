import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'api_service.dart';
import 'theme.dart';

class ComparisonPage extends StatefulWidget {
  final List<String> docIds;

  const ComparisonPage({super.key, required this.docIds});

  @override
  State<ComparisonPage> createState() => _ComparisonPageState();
}

class _ComparisonPageState extends State<ComparisonPage> {
  bool _isLoading = true;
  String? _error;
  Map<String, dynamic>? _comparisonData;

  @override
  void initState() {
    super.initState();
    _fetchComparison();
  }

  Future<void> _fetchComparison() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await ApiService.compareContracts(widget.docIds);
      setState(() {
        _comparisonData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Contract Comparison"),
        centerTitle: true,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text("AI is analyzing and comparing contracts...", 
                style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _fetchComparison,
                child: const Text("Retry"),
              ),
            ],
          ),
        ),
      );
    }

    final comparison = _comparisonData!["comparison"] as List<dynamic>;
    final summary = _comparisonData!["summary"] as String;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildAIInsights(summary),
          const SizedBox(height: 24),
          _buildComparisonTable(comparison),
          const SizedBox(height: 40),
        ],
      ),
    );
  }

  Widget _buildAIInsights(String summary) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.indigo.shade600, Colors.indigo.shade800],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.indigo.shade200,
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 10),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 12),
                const Text(
                  "AI Comparison Summary",
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: double.infinity,
            margin: const EdgeInsets.all(8),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
            ),
            child: MarkdownBody(
              data: summary,
              styleSheet: MarkdownStyleSheet(
                p: const TextStyle(fontSize: 15, height: 1.5, color: Colors.black87),
                strong: const TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildComparisonTable(List<dynamic> documents) {
    // Help access deeply nested data safely
    dynamic getSafe(dynamic data, List<String> path) {
      dynamic current = data;
      for (final key in path) {
        if (current == null || current is! Map) return null;
        current = current[key];
      }
      return current;
    }

    final keyFields = {
      "Monthly Payment": (d) => getSafe(d, ["data", "sla_fields", "financial", "monthly_rental"]),
      "Security Deposit": (d) => getSafe(d, ["data", "sla_fields", "financial", "security_deposit"]),
      "Lease Term": (d) => getSafe(d, ["data", "sla_fields", "financial", "lease_term"]),
      "Annual Mileage": (d) => getSafe(d, ["data", "sla_fields", "usage", "annual_mileage"]),
      "Excess Charge": (d) => getSafe(d, ["data", "sla_fields", "usage", "excess_charge"]),
      "Risk Score": (d) => getSafe(d, ["data", "risk_analysis", "contract_fairness_score"]) != null 
          ? "${getSafe(d, ["data", "risk_analysis", "contract_fairness_score"])}/100" 
          : "N/A",
      "Fairness Level": (d) => getSafe(d, ["data", "risk_analysis", "contract_fairness_level"]),
      "Lessor": (d) => getSafe(d, ["data", "sla_fields", "parties", "lessor_name"]),
      "Vehicle": (d) => getSafe(d, ["data", "sla_fields", "vehicle", "make"]) != null
          ? "${getSafe(d, ["data", "sla_fields", "vehicle", "year"]) ?? ""} ${getSafe(d, ["data", "sla_fields", "vehicle", "make"]) ?? ""} ${getSafe(d, ["data", "sla_fields", "vehicle", "model"]) ?? ""}"
          : "Unknown Vehicle",
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Side-by-Side Breakdown",
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: DataTable(
              columnSpacing: 24,
              headingRowColor: MaterialStateProperty.all(Colors.indigo.shade50),
              columns: [
                const DataColumn(label: Text("FIELD", style: TextStyle(fontWeight: FontWeight.bold))),
                ...documents.map((doc) => DataColumn(
                  label: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 150),
                    child: Text(
                      doc["filename"],
                      style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                )),
              ],
              rows: keyFields.entries.map((entry) {
                return DataRow(
                  cells: [
                    DataCell(Text(entry.key, style: TextStyle(fontWeight: FontWeight.w500, color: Colors.grey.shade700))),
                    ...documents.map((doc) {
                      final val = entry.value(doc);
                      return DataCell(Text(val?.toString() ?? "N/A"));
                    }),
                  ],
                );
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }
}

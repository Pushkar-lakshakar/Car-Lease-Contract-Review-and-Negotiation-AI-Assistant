import 'package:flutter/material.dart';
import 'theme.dart';
import 'dashboard_page.dart';
import 'login_page.dart';

void main() {
  runApp(const CarLeaseApp());
}

class CarLeaseApp extends StatelessWidget {
  const CarLeaseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Car Contract Analyzer',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const LoginPage(),
    );
  }
}

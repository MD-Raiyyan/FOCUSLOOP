import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/theme';

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  // Temporary mock login — no credentials verified, just navigates to the app
  const handleLogin = () => {
    if (email.length > 0 && password.length > 0) {
      router.replace('/(tabs)');
    }
  };

  // Temporary Google login — navigates to app directly
  const handleGoogleLogin = () => {
    router.replace('/(tabs)');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* ── Brand Header ── */}
          <View style={styles.brandRow}>
            <Ionicons name="infinite" size={28} color={Colors.primary} />
            <Text style={styles.brandText}>FOCUSLOOP</Text>
          </View>

          {/* ── Hero Illustration ── */}
          <View style={styles.illustrationWrapper}>
            <Image
              source={require('../../assets/images/login_illustration.png')}
              style={styles.illustration}
              resizeMode="contain"
            />
          </View>

          {/* ── Title & Subtitle ── */}
          <Text style={styles.title}>Welcome Back! 👋</Text>
          <Text style={styles.subtitle}>Log in to continue your focus journey.</Text>

          {/* ── Email Input ── */}
          <View style={styles.inputBox}>
            <Ionicons name="mail-outline" size={20} color="#9896B0" style={styles.inputIcon} />
            <TextInput
              style={styles.inputText}
              placeholder="Email or Username"
              placeholderTextColor="#9896B0"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              returnKeyType="next"
            />
          </View>

          {/* ── Password Input ── */}
          <View style={styles.inputBox}>
            <Ionicons name="lock-closed-outline" size={20} color="#9896B0" style={styles.inputIcon} />
            <TextInput
              style={styles.inputText}
              placeholder="Password"
              placeholderTextColor="#9896B0"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              returnKeyType="done"
              onSubmitEditing={handleLogin}
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              activeOpacity={0.7}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons
                name={showPassword ? 'eye-outline' : 'eye-off-outline'}
                size={20}
                color="#9896B0"
              />
            </TouchableOpacity>
          </View>

          {/* ── Remember Me & Forgot Password ── */}
          <View style={styles.optionsRow}>
            <TouchableOpacity
              style={styles.rememberRow}
              onPress={() => setRememberMe(!rememberMe)}
              activeOpacity={0.75}
            >
              <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
                {rememberMe && (
                  <Ionicons name="checkmark" size={13} color="#FFFFFF" />
                )}
              </View>
              <Text style={styles.rememberLabel}>Remember me</Text>
            </TouchableOpacity>

            <TouchableOpacity activeOpacity={0.7}>
              <Text style={styles.forgotText}>Forgot password?</Text>
            </TouchableOpacity>
          </View>

          {/* ── Log In Button ── */}
          <TouchableOpacity
            style={styles.loginBtn}
            onPress={handleLogin}
            activeOpacity={0.85}
          >
            <Ionicons name="arrow-forward" size={20} color="#FFFFFF" />
            <Text style={styles.loginBtnText}>Log In</Text>
          </TouchableOpacity>

          {/* ── OR Divider ── */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerLabel}>OR</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* ── Continue with Google ── */}
          <TouchableOpacity
            style={styles.googleBtn}
            onPress={handleGoogleLogin}
            activeOpacity={0.85}
          >
            {/* Google G icon using colored letters as substitute */}
            <View style={styles.googleIconContainer}>
              <Text style={styles.googleG}>G</Text>
            </View>
            <Text style={styles.googleBtnText}>Continue with Google</Text>
          </TouchableOpacity>

          {/* ── Sign Up Footer ── */}
          <View style={styles.signUpRow}>
            <Text style={styles.signUpPrompt}>Don't have an account?</Text>
            <TouchableOpacity activeOpacity={0.7}>
              <Text style={styles.signUpLink}> Sign Up</Text>
            </TouchableOpacity>
          </View>

          {/* ── Bottom Tagline ── */}
          <Text style={styles.tagline}>✦ Better Focus   ✦ A Healthier You</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safeArea: {
    flex: 1,
    backgroundColor: '#F3F1FB',
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 32,
    alignItems: 'center',
  },

  // Brand
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 20,
  },
  brandText: {
    fontSize: 19,
    fontWeight: '800',
    color: Colors.primary,
    letterSpacing: 2.5,
  },

  // Illustration
  illustrationWrapper: {
    width: '100%',
    height: 200,
    borderRadius: 28,
    backgroundColor: '#ECEAFC',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    marginBottom: 24,
  },
  illustration: {
    width: '100%',
    height: '100%',
  },

  // Title
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: '#1A1848',
    marginBottom: 6,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 24,
    textAlign: 'center',
  },

  // Input
  inputBox: {
    width: '100%',
    height: 54,
    backgroundColor: '#F5F3FF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  inputIcon: {
    marginRight: 12,
  },
  inputText: {
    flex: 1,
    fontSize: 15,
    color: '#1A1848',
  },

  // Options row
  optionsRow: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingHorizontal: 2,
  },
  rememberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 5,
    borderWidth: 1.5,
    borderColor: '#B0ADCC',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'transparent',
  },
  checkboxChecked: {
    backgroundColor: Colors.primaryContainer,
    borderColor: Colors.primaryContainer,
  },
  rememberLabel: {
    fontSize: 13,
    color: '#4B4869',
    fontWeight: '500',
  },
  forgotText: {
    fontSize: 13,
    color: Colors.primaryContainer,
    fontWeight: '600',
  },

  // Login button
  loginBtn: {
    width: '100%',
    height: 54,
    backgroundColor: Colors.primaryContainer,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 5,
  },
  loginBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },

  // Divider
  divider: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 18,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#DDD9F0',
  },
  dividerLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#A09DBF',
    marginHorizontal: 12,
    letterSpacing: 1,
  },

  // Google button
  googleBtn: {
    width: '100%',
    height: 54,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  googleIconContainer: {
    width: 22,
    height: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleG: {
    fontSize: 17,
    fontWeight: '800',
    color: '#4285F4',
  },
  googleBtnText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1848',
  },

  // Sign up
  signUpRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 22,
    marginBottom: 14,
  },
  signUpPrompt: {
    fontSize: 13,
    color: '#64748B',
  },
  signUpLink: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.primaryContainer,
  },

  // Tagline
  tagline: {
    fontSize: 11,
    fontWeight: '600',
    color: '#B5B2D4',
    letterSpacing: 0.4,
  },
});

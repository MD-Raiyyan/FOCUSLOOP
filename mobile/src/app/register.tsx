import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/theme';
import { useAuth } from '@/hooks/useAuth';

export default function RegisterScreen() {
  const router = useRouter();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRegister = async () => {
    setErrorMessage(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrorMessage('Please enter a valid email address.');
      return;
    }
    if (!password) {
      setErrorMessage('Please enter a password.');
      return;
    }
    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      await register({
        email: trimmedEmail,
        password,
        name: name.trim() || undefined,
        username: username.trim() || undefined,
      });
      router.replace('/onboarding' as any);
    } catch (err: any) {
      setErrorMessage(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
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

          {/* ── Title & Subtitle ── */}
          <Text style={styles.title}>Create Account 🚀</Text>
          <Text style={styles.subtitle}>
            Join FocusLoop to build behavioral intelligence and master your time.
          </Text>

          {/* ── Error Banner ── */}
          {errorMessage && (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle" size={18} color="#DC2626" />
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          {/* ── Full Name Input ── */}
          <View style={styles.inputBox}>
            <Ionicons name="person-outline" size={20} color="#9896B0" style={styles.inputIcon} />
            <TextInput
              style={styles.inputText}
              placeholder="Full Name (optional)"
              placeholderTextColor="#9896B0"
              value={name}
              onChangeText={setName}
              returnKeyType="next"
            />
          </View>

          {/* ── Username Input ── */}
          <View style={styles.inputBox}>
            <Ionicons name="at-outline" size={20} color="#9896B0" style={styles.inputIcon} />
            <TextInput
              style={styles.inputText}
              placeholder="Username (optional)"
              placeholderTextColor="#9896B0"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              returnKeyType="next"
            />
          </View>

          {/* ── Email Input ── */}
          <View style={styles.inputBox}>
            <Ionicons name="mail-outline" size={20} color="#9896B0" style={styles.inputIcon} />
            <TextInput
              style={styles.inputText}
              placeholder="Email address *"
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
              placeholder="Password (min 8 characters) *"
              placeholderTextColor="#9896B0"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              returnKeyType="next"
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

          {/* ── Confirm Password Input ── */}
          <View style={styles.inputBox}>
            <Ionicons name="shield-checkmark-outline" size={20} color="#9896B0" style={styles.inputIcon} />
            <TextInput
              style={styles.inputText}
              placeholder="Confirm Password *"
              placeholderTextColor="#9896B0"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showPassword}
              returnKeyType="done"
              onSubmitEditing={handleRegister}
            />
          </View>

          {/* ── Sign Up Button ── */}
          <TouchableOpacity
            style={[styles.primaryBtn, isSubmitting && styles.btnDisabled]}
            onPress={handleRegister}
            disabled={isSubmitting}
            activeOpacity={0.85}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <>
                <Ionicons name="person-add-outline" size={20} color="#FFFFFF" />
                <Text style={styles.primaryBtnText}>Create Account</Text>
              </>
            )}
          </TouchableOpacity>

          {/* ── Already have an account? ── */}
          <View style={styles.loginRow}>
            <Text style={styles.loginPrompt}>Already have an account?</Text>
            <TouchableOpacity onPress={() => router.push('/login')} activeOpacity={0.7}>
              <Text style={styles.loginLink}> Log In</Text>
            </TouchableOpacity>
          </View>

          {/* ── Bottom Tagline ── */}
          <Text style={styles.tagline}>✦ Grounded in Behavior Science ✦</Text>
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
    paddingTop: 24,
    paddingBottom: 40,
    alignItems: 'center',
  },
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
    lineHeight: 20,
    paddingHorizontal: 12,
  },
  errorBox: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 14,
    marginBottom: 16,
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: '#B91C1C',
    fontWeight: '500',
  },
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
  primaryBtn: {
    width: '100%',
    height: 54,
    backgroundColor: Colors.primaryContainer,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 12,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 5,
  },
  btnDisabled: {
    opacity: 0.65,
  },
  primaryBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  loginRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 16,
  },
  loginPrompt: {
    fontSize: 14,
    color: '#64748B',
  },
  loginLink: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.primaryContainer,
  },
  tagline: {
    fontSize: 11,
    fontWeight: '600',
    color: '#B5B2D4',
    letterSpacing: 0.4,
  },
});

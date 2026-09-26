import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { useRouter, usePathname } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/theme';

export interface TabItem {
  id: string;
  label: string;
  path: string;
  iconName: keyof typeof Ionicons.glyphMap;
}

const tabs: TabItem[] = [
  { id: 'today', label: 'Today', path: '/', iconName: 'sunny-outline' },
  { id: 'delay-log', label: 'Delay Log', path: '/delay-log', iconName: 'hourglass-outline' },
  { id: 'lab', label: 'Lab', path: '/lab', iconName: 'flask-outline' },
  { id: 'ai-coach', label: 'AI Coach', path: '/ai-coach', iconName: 'sparkles-outline' },
  { id: 'insights', label: 'Insights', path: '/insights', iconName: 'stats-chart-outline' },
];

export const BottomDock: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <View style={styles.dockWrapper} pointerEvents="box-none">
      <View style={styles.dockContainer}>
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.path ||
            (tab.path === '/' && (pathname === '/index' || pathname === '/(tabs)'));

          const activeIconName = (tab.iconName as string).endsWith('-outline')
            ? (tab.iconName as string).replace('-outline', '')
            : tab.iconName;

          return (
            <TouchableOpacity
              key={tab.id}
              style={[styles.tabButton, isActive && styles.tabButtonActive]}
              onPress={() => router.push(tab.path as any)}
              activeOpacity={0.8}
            >
              <Ionicons
                name={(isActive ? activeIconName : tab.iconName) as any}
                size={20}
                color={isActive ? Colors.primary : Colors.textSubtle}
              />
              <Text
                style={[
                  styles.tabLabel,
                  { color: isActive ? Colors.primary : Colors.textSubtle },
                  isActive && styles.tabLabelActive,
                ]}
              >
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  dockWrapper: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 24 : 16,
    left: 0,
    right: 0,
    alignItems: 'center',
    paddingHorizontal: 16,
    zIndex: 100,
  },
  dockContainer: {
    width: '100%',
    maxWidth: 440,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 6,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 8,
    borderWidth: 1,
    borderColor: 'rgba(238, 242, 246, 0.8)',
  },
  tabButton: {
    minWidth: 56,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
  },
  tabButtonActive: {
    backgroundColor: Colors.surfaceTintViolet,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '500',
    marginTop: 2,
  },
  tabLabelActive: {
    fontWeight: '700',
  },
});

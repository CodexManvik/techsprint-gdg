import { Mic, MicOff, PhoneOff } from 'lucide-react';
import { FloatingDock } from '../ui/floating-dock';

interface ControlBarProps {
  isMuted: boolean;
  onToggleMute: () => void;
  onEndInterview: () => void;
}

export const ControlBar = ({ isMuted, onToggleMute, onEndInterview }: ControlBarProps) => {
  const dockItems = [
    {
      title: isMuted ? 'Unmute' : 'Mute',
      icon: isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />,
      onClick: onToggleMute,
      active: !isMuted,
    },
    {
      title: 'End Interview',
      icon: <PhoneOff className="w-5 h-5" />,
      onClick: onEndInterview,
      danger: true,
    },
  ];

  return <FloatingDock items={dockItems} />;
};

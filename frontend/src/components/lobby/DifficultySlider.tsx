import { motion } from 'framer-motion';
import { useSessionStore, type DifficultyLevel } from '../../stores/sessionStore';
import { cn } from '../../lib/utils';

const DIFFICULTY_LEVELS: { value: number; label: DifficultyLevel; color: string; gradient: string }[] = [
  { value: 0, label: 'junior', color: '#22c55e', gradient: 'from-green-500 to-emerald-500' },
  { value: 1, label: 'mid', color: '#3a0ca3', gradient: 'from-primary to-accent-purple' },
  { value: 2, label: 'senior', color: '#f59e0b', gradient: 'from-amber-500 to-orange-500' },
  { value: 3, label: 'staff', color: '#ef4444', gradient: 'from-red-500 to-rose-500' },
];

export const DifficultySlider = () => {
  const { difficulty, setDifficulty } = useSessionStore();

  const currentIndex = DIFFICULTY_LEVELS.findIndex(d => d.label === difficulty);
  const currentLevel = DIFFICULTY_LEVELS[currentIndex];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const index = parseInt(e.target.value);
    setDifficulty(DIFFICULTY_LEVELS[index].label);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">Difficulty Level</label>
        <motion.span
          key={difficulty}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={cn(
            'px-4 py-1.5 rounded-full text-sm font-semibold text-white capitalize',
            `bg-gradient-to-r ${currentLevel.gradient}`
          )}
          style={{ boxShadow: `0 0 20px ${currentLevel.color}40` }}
        >
          {difficulty}
        </motion.span>
      </div>

      <div className="relative">
        {/* Track background */}
        <div className="absolute top-1/2 -translate-y-1/2 w-full h-2 rounded-full bg-surface-elevated" />

        {/* Active track with gradient */}
        <motion.div
          className={cn(
            'absolute top-1/2 -translate-y-1/2 h-2 rounded-full',
            `bg-gradient-to-r ${currentLevel.gradient}`
          )}
          style={{ width: `${(currentIndex / 3) * 100}%` }}
          initial={false}
          animate={{ width: `${(currentIndex / 3) * 100}%` }}
          transition={{ duration: 0.2 }}
        />

        {/* Glow effect */}
        <motion.div
          className="absolute top-1/2 -translate-y-1/2 h-2 rounded-full opacity-50 blur-sm"
          style={{
            width: `${(currentIndex / 3) * 100}%`,
            background: `linear-gradient(90deg, ${currentLevel.color}, ${currentLevel.color})`
          }}
        />

        <input
          type="range"
          min="0"
          max="3"
          step="1"
          value={currentIndex}
          onChange={handleChange}
          className="relative w-full h-2 appearance-none bg-transparent cursor-pointer z-10"
        />

        {/* Level indicators */}
        <div className="flex justify-between mt-3">
          {DIFFICULTY_LEVELS.map((level, index) => (
            <motion.button
              key={level.label}
              onClick={() => setDifficulty(level.label)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              className={cn(
                'text-xs font-medium capitalize px-2 py-1 rounded-lg transition-colors',
                index === currentIndex
                  ? 'text-foreground bg-surface-light'
                  : 'text-foreground-muted hover:text-foreground'
              )}
            >
              {level.label}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
};

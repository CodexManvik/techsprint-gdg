import { useSessionStore, type DifficultyLevel } from '../../stores/sessionStore';

const DIFFICULTY_LEVELS: { value: number; label: DifficultyLevel; color: string }[] = [
  { value: 0, label: 'junior', color: '#10B981' },
  { value: 1, label: 'mid', color: '#3B82F6' },
  { value: 2, label: 'senior', color: '#F59E0B' },
  { value: 3, label: 'staff', color: '#EF4444' },
];

export const DifficultySlider = () => {
  const { difficulty, setDifficulty } = useSessionStore();
  
  const currentIndex = DIFFICULTY_LEVELS.findIndex(d => d.label === difficulty);
  const currentColor = DIFFICULTY_LEVELS[currentIndex].color;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const index = parseInt(e.target.value);
    setDifficulty(DIFFICULTY_LEVELS[index].label);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-dark">Difficulty Level</label>
        <span
          className="px-3 py-1 rounded-full text-sm font-semibold text-white capitalize"
          style={{ backgroundColor: currentColor }}
        >
          {difficulty}
        </span>
      </div>
      
      <div className="relative">
        <input
          type="range"
          min="0"
          max="3"
          step="1"
          value={currentIndex}
          onChange={handleChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, ${currentColor} 0%, ${currentColor} ${(currentIndex / 3) * 100}%, #E5E7EB ${(currentIndex / 3) * 100}%, #E5E7EB 100%)`
          }}
        />
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          {DIFFICULTY_LEVELS.map((level) => (
            <span key={level.label} className="capitalize">{level.label}</span>
          ))}
        </div>
      </div>
    </div>
  );
};

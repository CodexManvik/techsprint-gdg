import { useEffect, useState } from 'react';
import { Camera, Mic, AlertCircle, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { useMediaPipe } from '../../hooks/useMediaPipe';
import { Button } from '../ui/Button';

export const TechCheck = ({ onComplete }: { onComplete: () => void }) => {
  const [cameraGranted, setCameraGranted] = useState(false);
  const [micGranted, setMicGranted] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const { videoRef, stopCamera } = useMediaPipe();

  useEffect(() => {
    checkPermissions();
    return () => stopCamera();
  }, [stopCamera]);

  const checkPermissions = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setCameraGranted(true);
      setMicGranted(true);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Permission denied:', error);
      setShowGuide(true);
    }
  };

  const canProceed = cameraGranted && micGranted;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-slate-dark mb-2">Tech Check</h2>
        <p className="text-gray-600">Let's make sure everything works before we start</p>
      </div>

      <div className="bg-white rounded-xl shadow-soft p-6 space-y-6">
        <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden relative">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          {!cameraGranted && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
              <Camera className="text-gray-400" size={64} />
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <Camera size={24} className="text-gray-600" />
              <span className="font-medium text-slate-dark">Camera</span>
            </div>
            {cameraGranted ? (
              <CheckCircle className="text-green-500" size={24} />
            ) : (
              <AlertCircle className="text-accent-amber" size={24} />
            )}
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <Mic size={24} className="text-gray-600" />
              <span className="font-medium text-slate-dark">Microphone</span>
            </div>
            {micGranted ? (
              <CheckCircle className="text-green-500" size={24} />
            ) : (
              <AlertCircle className="text-accent-amber" size={24} />
            )}
          </div>
        </div>

        {showGuide && !canProceed && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-amber-50 border border-accent-amber rounded-lg p-4"
          >
            <div className="flex gap-3">
              <AlertCircle className="text-accent-amber flex-shrink-0" size={24} />
              <div>
                <h4 className="font-semibold text-slate-dark mb-2">Permission Required</h4>
                <p className="text-sm text-gray-700 mb-3">
                  Click the camera icon in your browser's address bar and allow access to your camera and microphone.
                </p>
                <Button size="sm" onClick={checkPermissions}>
                  Try Again
                </Button>
              </div>
            </div>
          </motion.div>
        )}

        <Button
          onClick={onComplete}
          disabled={!canProceed}
          className="w-full"
          size="lg"
        >
          {canProceed ? 'Start Interview' : 'Waiting for permissions...'}
        </Button>
      </div>
    </div>
  );
};

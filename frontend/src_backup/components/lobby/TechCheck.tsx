import { useEffect, useState } from 'react';
import { Camera, Mic, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMediaPipe } from '../../hooks/useMediaPipe';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';

interface TechCheckProps {
  onComplete: () => void;
}

export const TechCheck = ({ onComplete }: TechCheckProps) => {
  const [cameraGranted, setCameraGranted] = useState(false);
  const [micGranted, setMicGranted] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [showGuide, setShowGuide] = useState(false);
  const { videoRef, stopCamera } = useMediaPipe();

  useEffect(() => {
    checkPermissions();
    return () => stopCamera();
  }, [stopCamera]);

  const checkPermissions = async () => {
    setIsChecking(true);
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
    } finally {
      setIsChecking(false);
    }
  };

  const canProceed = cameraGranted && micGranted;

  const StatusIndicator = ({ granted, checking }: { granted: boolean; checking: boolean }) => (
    <div className="relative">
      {checking ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <Loader2 className="w-6 h-6 text-primary" />
        </motion.div>
      ) : granted ? (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="relative"
        >
          <CheckCircle className="w-6 h-6 text-success" />
          <motion.div
            className="absolute inset-0 bg-success rounded-full"
            initial={{ scale: 1, opacity: 0.5 }}
            animate={{ scale: 2, opacity: 0 }}
            transition={{ duration: 0.5 }}
          />
        </motion.div>
      ) : (
        <AlertCircle className="w-6 h-6 text-warning" />
      )}
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h2 className="text-2xl font-bold text-foreground mb-2">Tech Check</h2>
        <p className="text-foreground-muted">Let's make sure everything works before we start</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass rounded-2xl p-6 space-y-6"
      >
        {/* Video preview */}
        <div className="aspect-video rounded-xl overflow-hidden relative border border-border">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          {!cameraGranted && (
            <div className="absolute inset-0 flex items-center justify-center bg-background-secondary">
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-20 h-20 rounded-full bg-surface-elevated flex items-center justify-center"
              >
                <Camera className="w-10 h-10 text-foreground-muted" />
              </motion.div>
            </div>
          )}

          {/* Gradient border when ready */}
          {canProceed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 rounded-xl pointer-events-none border-2 border-success"
              style={{ boxShadow: '0 0 20px rgba(34, 197, 94, 0.3)' }}
            />
          )}
        </div>

        {/* Permission status */}
        <div className="space-y-3">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className={cn(
              'flex items-center justify-between p-4 rounded-xl transition-colors',
              cameraGranted ? 'bg-success/10' : 'bg-surface-light'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center',
                cameraGranted ? 'bg-success/20' : 'bg-surface-elevated'
              )}>
                <Camera className={cn(
                  'w-5 h-5',
                  cameraGranted ? 'text-success' : 'text-foreground-muted'
                )} />
              </div>
              <span className="font-medium text-foreground">Camera</span>
            </div>
            <StatusIndicator granted={cameraGranted} checking={isChecking} />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className={cn(
              'flex items-center justify-between p-4 rounded-xl transition-colors',
              micGranted ? 'bg-success/10' : 'bg-surface-light'
            )}
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center',
                micGranted ? 'bg-success/20' : 'bg-surface-elevated'
              )}>
                <Mic className={cn(
                  'w-5 h-5',
                  micGranted ? 'text-success' : 'text-foreground-muted'
                )} />
              </div>
              <span className="font-medium text-foreground">Microphone</span>
            </div>
            <StatusIndicator granted={micGranted} checking={isChecking} />
          </motion.div>
        </div>

        {/* Permission guide */}
        <AnimatePresence>
          {showGuide && !canProceed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="bg-warning/10 border border-warning/30 rounded-xl p-4">
                <div className="flex gap-3">
                  <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">Permission Required</h4>
                    <p className="text-sm text-foreground-muted mb-3">
                      Click the camera icon in your browser's address bar and allow access to your camera and microphone.
                    </p>
                    <Button size="sm" variant="secondary" onClick={checkPermissions}>
                      Try Again
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Start button */}
        <Button
          onClick={onComplete}
          disabled={!canProceed}
          variant="gradient"
          className="w-full"
          size="lg"
        >
          {isChecking ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Checking permissions...
            </>
          ) : canProceed ? (
            '🚀 Start Interview'
          ) : (
            'Waiting for permissions...'
          )}
        </Button>
      </motion.div>
    </div>
  );
};

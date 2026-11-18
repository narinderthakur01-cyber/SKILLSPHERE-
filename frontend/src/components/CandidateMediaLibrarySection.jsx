import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, Search, Play, RefreshCw, Clock, HardDrive,
  CheckCircle2, X, Shield, AlertCircle
} from 'lucide-react';
import { mediaAPI } from '../services/api';
import { useToast } from './MotionComponents';

export const CandidateMediaLibrarySection = () => {
  const { addToast } = useToast();

  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedFolder, setSelectedFolder] = useState('');

  // Video Player Modal
  const [playingAsset, setPlayingAsset] = useState(null);
  const [signedPlaybackUrl, setSignedPlaybackUrl] = useState('');
  const [loadingPlayback, setLoadingPlayback] = useState(false);
  const [mediaError, setMediaError] = useState(false);

  const fetchAssets = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (selectedFolder) params.folder = selectedFolder;

      const res = await mediaAPI.list(params);
      setAssets(res.data || []);
    } catch (err) {
      console.error('Failed to load candidate media:', err);
      const msg = err.response?.data?.detail || 'Could not retrieve your media assets.';
      setError(msg);
      addToast({
        title: 'Media Library Error',
        message: msg,
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [selectedFolder]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchAssets();
  };

  const handleWatchVideo = async (asset) => {
    setPlayingAsset(asset);
    setMediaError(asset.upload_status === 'FAILED');
    setLoadingPlayback(true);
    try {
      const res = await mediaAPI.getSignedPlayback(asset.id);
      const url = res.data.playback_url || res.data.secure_url || asset.secure_url;
      setSignedPlaybackUrl(url);
      if (res.data.upload_status === 'FAILED') {
        setMediaError(true);
      }
    } catch (err) {
      console.warn("Could not generate playback token:", err);
      if (asset.secure_url || asset.playback_url) {
        setSignedPlaybackUrl(asset.playback_url || asset.secure_url);
      } else {
        setMediaError(true);
      }
    } finally {
      setLoadingPlayback(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) return `${mb.toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* 1. Header */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold text-charcoal dark:text-ivory flex items-center gap-2.5">
            <Film className="w-6 h-6 text-oxblood dark:text-rose" />
            <span>My Recordings & Media</span>
          </h2>
          <p className="text-xs text-slate/70 dark:text-ivory/65 font-mono mt-1">
            Cloudinary-backed encrypted media &bull; Time-limited authenticated streaming &bull; Your video assessment answers and test recordings
          </p>
        </div>

        <button
          onClick={fetchAssets}
          disabled={loading}
          className="p-2.5 rounded-xl border border-slate/15 dark:border-rose/15 text-slate/70 dark:text-ivory/70 hover:text-oxblood transition flex items-center gap-1.5 text-xs font-mono"
          title="Refresh media"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* 2. Search & Filters */}
      <div className="glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 flex flex-col sm:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate/40 dark:text-ivory/40" />
          <input
            type="text"
            placeholder="Search recordings by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-white dark:bg-charcoal-700 border border-slate/20 dark:border-white/10 text-xs text-charcoal dark:text-ivory outline-none focus:border-oxblood font-mono"
          />
        </form>

        <div className="flex items-center gap-2">
          <select
            value={selectedFolder}
            onChange={(e) => setSelectedFolder(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white dark:bg-charcoal-700 border border-slate/20 dark:border-white/10 text-xs text-charcoal dark:text-ivory font-mono outline-none focus:border-oxblood"
          >
            <option value="">All Media Categories</option>
            <option value="candidate-responses">Video Assessment Responses</option>
            <option value="assessments">Screening Test Recordings</option>
            <option value="resumes">Resumes & Documents</option>
          </select>
        </div>
      </div>

      {/* 3. Error Banner */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose/10 border border-rose/30 text-rose flex items-center gap-3 text-xs font-mono">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span className="flex-1">{error}</span>
          <button
            onClick={fetchAssets}
            className="px-3 py-1 rounded-lg bg-rose/20 hover:bg-rose/30 text-rose font-bold uppercase text-[10px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* 4. Assets Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div key={n} className="glass-card rounded-2xl p-4 space-y-3 animate-pulse border border-slate/10 dark:border-rose/10">
              <div className="w-full aspect-video rounded-xl bg-slate/10 dark:bg-white/5" />
              <div className="h-4 bg-slate/10 dark:bg-white/5 rounded w-3/4" />
              <div className="h-3 bg-slate/10 dark:bg-white/5 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : assets.length === 0 ? (
        <div className="glass-card p-12 rounded-3xl border border-slate/15 dark:border-rose/15 text-center space-y-3">
          <Film className="w-12 h-12 mx-auto text-slate/30 dark:text-ivory/30" />
          <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">
            No Recordings in Your Library Yet
          </h3>
          <p className="text-xs text-slate/60 dark:text-ivory/60 font-mono max-w-md mx-auto">
            When you complete video-based assessments or submit recorded screening responses, your securely archived Cloudinary media will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {assets.map((asset) => {
            const isVideo = asset.resource_type === 'video' ||
              ['mp4', 'webm', 'ogg', 'mov'].includes(asset.file_format?.toLowerCase());
            const isImage = asset.resource_type === 'image' ||
              ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(asset.file_format?.toLowerCase());
            const isFailed = asset.upload_status === 'FAILED';

            return (
              <motion.div
                key={asset.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`glass-card rounded-2xl overflow-hidden border shadow-md flex flex-col group transition ${
                  isFailed
                    ? 'border-red-500/30 hover:border-red-500/60 bg-red-500/5'
                    : 'border-slate/15 dark:border-rose/15 hover:border-oxblood/40'
                }`}
              >
                {/* Thumbnail / Preview Area */}
                <div className="relative aspect-video bg-charcoal-900 overflow-hidden flex items-center justify-center">
                  {asset.thumbnail_url && !isFailed ? (
                    <img
                      src={asset.thumbnail_url}
                      alt={asset.original_filename}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : null}

                  {/* Fallback Graphic */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-ivory/40 pointer-events-none">
                    {isFailed ? (
                      <div className="flex flex-col items-center text-red-400">
                        <AlertCircle className="w-8 h-8 mb-1" />
                        <span className="font-mono text-[10px] uppercase font-bold">Storage Missing</span>
                      </div>
                    ) : isVideo ? (
                      <div className="flex flex-col items-center">
                        <Film className="w-8 h-8 mb-1" />
                        <span className="font-mono text-[10px] uppercase">{asset.file_format || 'Video'}</span>
                      </div>
                    ) : isImage ? (
                      <div className="flex flex-col items-center">
                        <Film className="w-8 h-8 mb-1" />
                        <span className="font-mono text-[10px] uppercase">{asset.file_format || 'Image'}</span>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center">
                        <Film className="w-8 h-8 mb-1" />
                        <span className="font-mono text-[10px] uppercase">{asset.file_format || 'File'}</span>
                      </div>
                    )}
                  </div>

                  {/* Duration Badge */}
                  {asset.video_duration_seconds > 0 && (
                    <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 text-[10px] font-mono font-bold text-ivory flex items-center gap-1 backdrop-blur-sm">
                      <Clock className="w-2.5 h-2.5 text-rose" />
                      {formatDuration(asset.video_duration_seconds)}
                    </span>
                  )}

                  {/* Play/View Button Overlay */}
                  <button
                    onClick={() => handleWatchVideo(asset)}
                    className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-oxblood/90 text-ivory flex items-center justify-center shadow-xl opacity-90 group-hover:opacity-100 group-hover:scale-110 transition"
                    title={isVideo ? "Play recording" : "Preview file"}
                  >
                    <Play className="w-5 h-5 fill-ivory ml-0.5" />
                  </button>
                </div>

                {/* Card Body */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div>
                    <h4 className="font-display text-sm font-bold text-charcoal dark:text-ivory truncate" title={asset.original_filename}>
                      {asset.original_filename}
                    </h4>
                    <p className="text-[10px] font-mono text-slate/50 dark:text-ivory/40 truncate mt-0.5">
                      {asset.folder}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate/10 dark:border-white/5 flex items-center justify-between text-[11px] font-mono text-slate/60 dark:text-ivory/60">
                    <span className="flex items-center gap-1">
                      <HardDrive className="w-3 h-3 text-oxblood dark:text-rose" />
                      {formatFileSize(asset.file_size_bytes)}
                    </span>

                    {isFailed ? (
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-1">
                        <AlertCircle className="w-2.5 h-2.5" />
                        Unavailable
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        Archived
                      </span>
                    )}
                  </div>

                  <button
                    onClick={() => handleWatchVideo(asset)}
                    className="w-full py-2 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-oxblood hover:text-ivory text-xs font-display font-semibold transition flex items-center justify-center gap-1.5"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>{isVideo ? 'Watch Recording' : isImage ? 'View Image' : 'View File'}</span>
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* 5. Secure Media Player & Viewer Modal */}
      <AnimatePresence>
        {playingAsset && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel w-full max-w-3xl rounded-3xl overflow-hidden shadow-2xl border border-ivory/20 flex flex-col bg-charcoal-900"
            >
              <div className="p-4 bg-black/60 border-b border-ivory/10 flex justify-between items-center text-ivory">
                <div className="flex items-center gap-2 truncate">
                  <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="font-display text-sm font-bold truncate max-w-md">
                    {playingAsset.original_filename}
                  </span>
                </div>
                <button
                  onClick={() => {
                    setPlayingAsset(null);
                    setSignedPlaybackUrl('');
                    setMediaError(false);
                  }}
                  className="p-1 rounded-lg hover:bg-ivory/10 transition text-ivory/70 hover:text-ivory"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Viewport */}
              <div className="min-h-[300px] max-h-[60vh] bg-black flex items-center justify-center relative">
                {loadingPlayback ? (
                  <div className="text-center space-y-2 text-ivory p-8">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-oxblood" />
                    <p className="text-xs font-mono">Connecting to Cloudinary stream...</p>
                  </div>
                ) : mediaError ? (
                  /* Informative error card */
                  <div className="p-8 text-center space-y-3 max-w-md mx-auto">
                    <div className="w-12 h-12 rounded-2xl bg-rose/15 text-rose flex items-center justify-center mx-auto border border-rose/30">
                      <AlertCircle className="w-6 h-6 text-rose" />
                    </div>
                    <div>
                      <h4 className="font-display font-bold text-sm text-white">Playback Unavailable</h4>
                      <p className="text-xs font-mono text-ivory/70 mt-1">
                        This recording could not be loaded from Cloudinary storage.
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-black/60 border border-ivory/10 text-[10px] font-mono text-left space-y-1 text-ivory/75">
                      <div><span className="text-ivory/40">File:</span> {playingAsset.original_filename}</div>
                      <div><span className="text-ivory/40">Status:</span> <span className="text-amber-400 uppercase font-bold">{playingAsset.upload_status || 'UNAVAILABLE'}</span></div>
                      <div className="truncate"><span className="text-ivory/40">URL:</span> {signedPlaybackUrl || playingAsset.secure_url}</div>
                    </div>
                    <div className="pt-2 flex justify-center gap-2">
                      <button
                        onClick={() => {
                          setMediaError(false);
                          handleWatchVideo(playingAsset);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-mono text-white flex items-center gap-1 transition"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Retry</span>
                      </button>
                      {playingAsset.secure_url && (
                        <a
                          href={playingAsset.secure_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1.5 rounded-lg bg-oxblood/80 hover:bg-oxblood text-xs font-mono text-white transition"
                        >
                          Open Direct URL
                        </a>
                      )}
                    </div>
                  </div>
                ) : signedPlaybackUrl ? (
                  playingAsset.resource_type === 'image' ||
                  ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(playingAsset.file_format?.toLowerCase()) ? (
                    <div className="p-4 flex items-center justify-center w-full h-full">
                      <img
                        src={signedPlaybackUrl}
                        alt={playingAsset.original_filename}
                        className="max-h-[55vh] max-w-full object-contain rounded-xl shadow-2xl"
                        onError={() => setMediaError(true)}
                      />
                    </div>
                  ) : (
                    <video
                      src={signedPlaybackUrl}
                      controls
                      autoPlay
                      playsInline
                      className="w-full h-full max-h-[55vh] object-contain"
                      onError={() => setMediaError(true)}
                    />
                  )
                ) : (
                  <p className="text-xs font-mono text-rose">Failed to load media stream.</p>
                )}
              </div>

              <div className="p-3.5 bg-black/40 text-[11px] font-mono text-ivory/60 flex items-center justify-between border-t border-ivory/10">
                <span>Access: Authenticated Signed Token</span>
                <span>Format: {playingAsset.file_format?.toUpperCase() || 'MP4'}</span>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

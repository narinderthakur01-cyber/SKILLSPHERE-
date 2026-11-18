import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Film, Search, Filter, Play, Trash2, Upload, RefreshCw,
  Folder, Clock, FileText, CheckCircle2, AlertTriangle, X,
  Shield, ExternalLink, HardDrive, Eye
} from 'lucide-react';
import { mediaAPI } from '../services/api';
import { useToast } from './MotionComponents';

export const RecruiterMediaLibraryTab = () => {
  const { addToast } = useToast();

  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedFolder, setSelectedFolder] = useState('');
  const [selectedType, setSelectedType] = useState('');

  // Video Player Modal
  const [playingAsset, setPlayingAsset] = useState(null);
  const [signedPlaybackUrl, setSignedPlaybackUrl] = useState('');
  const [loadingPlayback, setLoadingPlayback] = useState(false);
  const [mediaError, setMediaError] = useState(false);

  // Deletion Modal
  const [assetToDelete, setAssetToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Upload Modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadFolder, setUploadFolder] = useState('interviews');
  const [uploading, setUploading] = useState(false);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (selectedFolder) params.folder = selectedFolder;
      if (selectedType) params.resource_type = selectedType;

      const res = await mediaAPI.list(params);
      setAssets(res.data);
    } catch (err) {
      addToast({
        title: "Media Library Error",
        message: err.response?.data?.detail || "Could not retrieve media assets.",
        type: "error"
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [selectedFolder, selectedType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchAssets();
  };

  // Open Media Player / Viewer
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
      // Fallback to asset's own stored URL if present
      if (asset.secure_url || asset.playback_url) {
        setSignedPlaybackUrl(asset.playback_url || asset.secure_url);
      } else {
        setMediaError(true);
      }
    } finally {
      setLoadingPlayback(false);
    }
  };

  // Confirm and Delete Asset
  const handleDeleteConfirm = async () => {
    if (!assetToDelete) return;
    setDeleting(true);
    try {
      await mediaAPI.delete(assetToDelete.id);
      addToast({
        title: "Asset Deleted",
        message: "Media asset was removed from Cloudinary and database.",
        type: "success"
      });
      setAssetToDelete(null);
      fetchAssets();
    } catch (err) {
      addToast({
        title: "Deletion Failed",
        message: err.response?.data?.detail || "Could not delete media asset.",
        type: "error"
      });
    } finally {
      setDeleting(false);
    }
  };

  // Handle Upload
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('folder_key', uploadFolder);

      await mediaAPI.uploadDirect(formData);
      addToast({
        title: "Upload Successful",
        message: "Asset uploaded and registered in Media Library.",
        type: "success"
      });
      setShowUploadModal(false);
      setUploadFile(null);
      fetchAssets();
    } catch (err) {
      addToast({
        title: "Upload Error",
        message: err.response?.data?.detail || "Failed to upload file.",
        type: "error"
      });
    } finally {
      setUploading(false);
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
      {/* 1. Header & Quick Actions */}
      <div className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold text-charcoal dark:text-ivory flex items-center gap-2.5">
            <Film className="w-6 h-6 text-oxblood dark:text-rose" />
            <span>Recruitment Media Library</span>
          </h2>
          <p className="text-xs text-slate/70 dark:text-ivory/65 font-mono mt-1">
            Cloudinary-backed storage &bull; Signed time-limited playback &bull; Interview recordings & candidate responses
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-oxblood px-4 py-2 rounded-xl text-xs font-display font-semibold flex items-center gap-1.5 shadow-lg"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Media</span>
          </button>
          <button
            onClick={fetchAssets}
            className="p-2 rounded-xl border border-slate/15 dark:border-rose/15 text-slate/70 dark:text-ivory/70 hover:text-oxblood transition"
            title="Refresh assets"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. Filters & Search Bar */}
      <div className="glass-card p-4 rounded-2xl border border-slate/15 dark:border-rose/15 flex flex-col md:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate/40 dark:text-ivory/40" />
          <input
            type="text"
            placeholder="Search by filename or public ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15 text-xs text-charcoal dark:text-ivory outline-none focus:border-oxblood font-mono"
          />
        </form>

        <div className="flex items-center gap-2">
          <select
            value={selectedFolder}
            onChange={(e) => setSelectedFolder(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white dark:bg-charcoal-700 border border-slate/30 dark:border-white/20 text-xs text-charcoal dark:text-ivory font-mono outline-none focus:border-oxblood"
          >
            <option value="" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">All Folders</option>
            <option value="interviews" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">skillsphere/interviews</option>
            <option value="candidate-responses" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">skillsphere/candidate-responses</option>
            <option value="assessments" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">skillsphere/assessments</option>
            <option value="resumes" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">skillsphere/resumes</option>
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 rounded-xl bg-white dark:bg-charcoal-700 border border-slate/30 dark:border-white/20 text-xs text-charcoal dark:text-ivory font-mono outline-none focus:border-oxblood"
          >
            <option value="" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">All Types</option>
            <option value="video" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Videos</option>
            <option value="image" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Images</option>
            <option value="raw" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Documents</option>
          </select>
        </div>
      </div>

      {/* 3. Media Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-56 glass-card rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : assets.length === 0 ? (
        <div className="text-center py-16 rounded-3xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-rose/15">
          <Film className="w-12 h-12 text-slate/30 dark:text-ivory/30 mx-auto mb-3" />
          <h3 className="font-display font-bold text-base text-charcoal dark:text-ivory">No Media Assets Found</h3>
          <p className="text-xs text-slate/60 dark:text-ivory/60 font-mono mt-1 max-w-sm mx-auto">
            Interview recordings, video assessment submissions, and uploaded attachments will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {assets.map((asset) => {
            const isVideo = asset.resource_type === 'video' ||
              ['mp4', 'webm', 'ogg', 'mov'].includes(asset.file_format?.toLowerCase());
            const isImage = asset.resource_type === 'image' ||
              ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(asset.file_format?.toLowerCase());
            const isFailed = asset.upload_status === 'FAILED';

            return (
              <div
                key={asset.id}
                className={`glass-card rounded-2xl border transition group flex flex-col justify-between overflow-hidden shadow-md ${
                  isFailed
                    ? 'border-red-500/30 hover:border-red-500/60 bg-red-500/5'
                    : 'border-slate/15 dark:border-rose/15 hover:border-oxblood/40'
                }`}
              >
                <div>
                  {/* Thumbnail / Preview Area */}
                  <div className="relative aspect-video bg-charcoal/90 flex items-center justify-center overflow-hidden">
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
                          <AlertTriangle className="w-8 h-8 mb-1" />
                          <span className="font-mono text-[10px] uppercase font-bold">Storage Missing</span>
                        </div>
                      ) : isVideo ? (
                        <div className="flex flex-col items-center">
                          <Film className="w-8 h-8 mb-1" />
                          <span className="font-mono text-[10px] uppercase">{asset.file_format || 'Video'}</span>
                        </div>
                      ) : isImage ? (
                        <div className="flex flex-col items-center">
                          <Eye className="w-8 h-8 mb-1" />
                          <span className="font-mono text-[10px] uppercase">{asset.file_format || 'Image'}</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center">
                          <FileText className="w-8 h-8 mb-1" />
                          <span className="font-mono text-[10px] uppercase">{asset.file_format || 'Document'}</span>
                        </div>
                      )}
                    </div>

                    {/* Interactive Click Overlay */}
                    <button
                      onClick={() => handleWatchVideo(asset)}
                      className="absolute inset-0 bg-black/40 hover:bg-black/20 flex items-center justify-center transition"
                      title={isVideo ? "Play video" : "Preview media"}
                    >
                      <div className="w-12 h-12 rounded-full bg-oxblood/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition">
                        {isVideo ? <Play className="w-5 h-5 ml-0.5" /> : <Eye className="w-5 h-5" />}
                      </div>
                    </button>

                    {asset.video_duration_seconds > 0 && (
                      <div className="absolute bottom-2 right-2 bg-black/80 px-2 py-0.5 rounded text-[10px] font-mono text-white flex items-center gap-1">
                        <Clock className="w-2.5 h-2.5 text-rose" />
                        <span>{formatDuration(asset.video_duration_seconds)}</span>
                      </div>
                    )}

                    {/* Media Type Tag */}
                    <div className="absolute top-2 left-2 bg-black/70 px-2 py-0.5 rounded text-[9px] font-mono uppercase tracking-wider text-ivory/80">
                      {asset.resource_type || (isVideo ? 'video' : isImage ? 'image' : 'raw')}
                    </div>
                  </div>

                  {/* Info Area */}
                  <div className="p-4 space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[10px] text-oxblood dark:text-rose font-bold truncate">
                        {asset.folder}
                      </span>
                      {isFailed ? (
                        <span className="font-mono text-[9px] px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-bold border border-red-500/30">
                          Unavailable
                        </span>
                      ) : (
                        <span className="badge-slate font-mono text-[9px] px-2 py-0.5 rounded">
                          {formatFileSize(asset.file_size_bytes)}
                        </span>
                      )}
                    </div>

                    <h4 className="font-display font-bold text-sm text-charcoal dark:text-ivory truncate" title={asset.original_filename}>
                      {asset.original_filename}
                    </h4>

                    <div className="flex items-center justify-between text-[11px] font-mono text-slate/50 dark:text-ivory/50 pt-2 border-t border-slate/10 dark:border-rose/10">
                      <span>{new Date(asset.created_at).toLocaleDateString()}</span>
                      <span className={`text-[10px] uppercase font-bold ${isFailed ? 'text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                        {isFailed ? 'Sync Failed' : (asset.access_classification || 'Confidential')}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions Footer */}
                <div className="p-3 bg-slate/5 dark:bg-white/5 border-t border-slate/15 dark:border-rose/15 flex justify-between items-center">
                  <button
                    onClick={() => handleWatchVideo(asset)}
                    className="text-xs font-mono font-bold text-oxblood dark:text-rose hover:underline flex items-center gap-1"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>{isVideo ? 'Play Video' : isImage ? 'View Image' : 'View File'}</span>
                  </button>
                  <button
                    onClick={() => setAssetToDelete(asset)}
                    className="p-1.5 rounded-lg text-slate/40 dark:text-ivory/40 hover:text-red-500 hover:bg-red-500/10 transition"
                    title="Delete asset"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MEDIA PLAYER & VIEWER MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {playingAsset && (
          <div className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-4xl w-full p-6 rounded-3xl border border-oxblood/40 space-y-4 bg-[#141820] text-ivory shadow-2xl"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="truncate">
                  <h3 className="font-display font-bold text-lg text-white truncate" title={playingAsset.original_filename}>
                    {playingAsset.original_filename}
                  </h3>
                  <p className="text-xs font-mono text-ivory/60 mt-0.5">
                    Cloudinary Storage &bull; Folder: {playingAsset.folder} &bull; Classification: {playingAsset.access_classification}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {playingAsset.secure_url && (
                    <a
                      href={playingAsset.secure_url}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1.5 rounded-lg text-ivory/60 hover:text-white hover:bg-white/10 transition"
                      title="Open Cloudinary delivery URL"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                  <button
                    onClick={() => {
                      setPlayingAsset(null);
                      setSignedPlaybackUrl('');
                      setMediaError(false);
                    }}
                    className="p-1.5 rounded-lg text-ivory/60 hover:text-white hover:bg-white/10 transition"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Main Media Viewer Viewport */}
              <div className="rounded-2xl overflow-hidden bg-black/90 min-h-[320px] max-h-[65vh] flex items-center justify-center border border-ivory/10 relative">
                {loadingPlayback ? (
                  <div className="flex flex-col items-center justify-center space-y-3 p-8">
                    <div className="w-9 h-9 rounded-full border-2 border-oxblood/30 border-t-oxblood animate-spin" />
                    <span className="font-mono text-xs text-ivory/70">Connecting to Cloudinary Media Stream...</span>
                  </div>
                ) : mediaError ? (
                  /* Informative Broken / Missing Media State - Never a blank black box */
                  <div className="p-8 text-center space-y-4 max-w-lg mx-auto">
                    <div className="w-14 h-14 rounded-2xl bg-rose/15 text-rose flex items-center justify-center mx-auto border border-rose/30">
                      <AlertTriangle className="w-7 h-7 text-rose" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-display font-bold text-base text-white">Cloudinary Stream Unavailable</h4>
                      <p className="text-xs font-mono text-ivory/70 leading-relaxed">
                        The media file could not be retrieved from Cloudinary storage. The asset does not exist on CDN or API credentials require configuration.
                      </p>
                    </div>

                    <div className="p-3.5 rounded-xl bg-black/60 border border-ivory/10 text-[11px] font-mono text-left space-y-1.5 text-ivory/80">
                      <div className="flex justify-between">
                        <span className="text-ivory/50">Asset ID:</span>
                        <span className="text-white font-mono">{playingAsset.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-ivory/50">Public ID:</span>
                        <span className="text-rose font-semibold truncate max-w-xs">{playingAsset.public_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-ivory/50">Upload Status:</span>
                        <span className="uppercase text-amber-400 font-bold">{playingAsset.upload_status || 'UNAVAILABLE'}</span>
                      </div>
                      <div className="truncate pt-1 border-t border-ivory/10">
                        <span className="text-ivory/50">Target URL: </span>
                        <a
                          href={signedPlaybackUrl || playingAsset.secure_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-oxblood dark:text-rose underline"
                        >
                          {signedPlaybackUrl || playingAsset.secure_url}
                        </a>
                      </div>
                    </div>

                    <div className="flex items-center justify-center gap-3 pt-2">
                      <button
                        onClick={() => {
                          setMediaError(false);
                          handleWatchVideo(playingAsset);
                        }}
                        className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-mono font-bold flex items-center gap-1.5 transition text-white"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Retry Stream</span>
                      </button>
                      {playingAsset.secure_url && (
                        <a
                          href={playingAsset.secure_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-4 py-2 rounded-xl bg-oxblood/80 hover:bg-oxblood text-xs font-mono font-bold flex items-center gap-1.5 text-white transition"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Open in New Tab</span>
                        </a>
                      )}
                    </div>
                  </div>
                ) : signedPlaybackUrl ? (
                  /* Render by media type */
                  playingAsset.resource_type === 'image' ||
                  ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(playingAsset.file_format?.toLowerCase()) ? (
                    <div className="p-4 flex items-center justify-center w-full h-full">
                      <img
                        src={signedPlaybackUrl}
                        alt={playingAsset.original_filename}
                        className="max-h-[60vh] max-w-full object-contain rounded-xl shadow-2xl"
                        onError={() => setMediaError(true)}
                      />
                    </div>
                  ) : playingAsset.resource_type === 'video' ||
                    ['mp4', 'webm', 'ogg', 'mov'].includes(playingAsset.file_format?.toLowerCase()) ? (
                    <video
                      src={signedPlaybackUrl}
                      controls
                      autoPlay
                      playsInline
                      className="w-full h-full max-h-[60vh] object-contain"
                      onError={() => setMediaError(true)}
                    />
                  ) : (
                    /* Document preview fallback */
                    <div className="p-12 text-center space-y-4">
                      <FileText className="w-16 h-16 text-oxblood dark:text-rose mx-auto" />
                      <div>
                        <h4 className="font-display font-bold text-base text-white">{playingAsset.original_filename}</h4>
                        <p className="text-xs font-mono text-ivory/60 mt-1">
                          Document &bull; {formatFileSize(playingAsset.file_size_bytes)}
                        </p>
                      </div>
                      <a
                        href={signedPlaybackUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-oxblood px-5 py-2.5 rounded-xl text-xs font-display font-semibold inline-flex items-center gap-2"
                      >
                        <ExternalLink className="w-4 h-4" />
                        <span>Open Document</span>
                      </a>
                    </div>
                  )
                ) : (
                  <div className="p-8 text-center text-rose font-mono text-xs">
                    Media stream unavailable.
                  </div>
                )}
              </div>

              {/* Modal Metadata Footer */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center text-xs font-mono text-ivory/60 pt-2 border-t border-ivory/10 gap-2">
                <span className="truncate">Public ID: {playingAsset.public_id}</span>
                <div className="flex items-center gap-3 shrink-0">
                  <span>Type: <strong className="text-white uppercase">{playingAsset.resource_type}</strong></span>
                  <span>Format: <strong className="text-white uppercase">{playingAsset.file_format || 'N/A'}</strong></span>
                  <span>Size: <strong className="text-white">{formatFileSize(playingAsset.file_size_bytes)}</strong></span>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* CONFIRM DELETION MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {assetToDelete && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-md w-full p-6 rounded-3xl border border-red-500/40 space-y-4 bg-[#141820] text-ivory"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-base text-white">Delete Media Asset</h3>
                  <p className="text-xs font-mono text-ivory/60">This action is permanent.</p>
                </div>
              </div>

              <p className="text-xs text-ivory/80 font-sans leading-relaxed">
                Are you sure you want to delete <strong>{assetToDelete.original_filename}</strong>? The file will be removed from Cloudinary and soft-deleted from the database.
              </p>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setAssetToDelete(null)}
                  className="flex-1 py-2.5 rounded-xl border border-ivory/20 font-mono text-xs text-ivory hover:bg-ivory/10"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  disabled={deleting}
                  className="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 font-display font-semibold text-xs text-white"
                >
                  {deleting ? "Deleting..." : "Confirm Delete"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ==================================================================== */}
      {/* DIRECT UPLOAD MODAL */}
      {/* ==================================================================== */}
      <AnimatePresence>
        {showUploadModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-card max-w-md w-full p-6 rounded-3xl border border-oxblood/40 space-y-4 bg-[#141820] text-ivory"
            >
              <div className="flex justify-between items-center pb-2 border-b border-ivory/10">
                <h3 className="font-display font-bold text-base text-white flex items-center gap-2">
                  <Upload className="w-4 h-4 text-oxblood dark:text-rose" />
                  <span>Upload Media Asset</span>
                </h3>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="p-1 rounded-lg text-ivory/60 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs font-sans">
                <div>
                  <label className="font-mono text-ivory/80 block mb-1">Target Cloudinary Folder</label>
                  <select
                    value={uploadFolder}
                    onChange={(e) => setUploadFolder(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-black/40 border border-ivory/15 font-mono text-xs text-ivory outline-none focus:border-oxblood"
                  >
                    <option value="interviews">skillsphere/interviews</option>
                    <option value="assessments">skillsphere/assessments</option>
                    <option value="interview_attachments">skillsphere/interview-attachments</option>
                  </select>
                </div>

                <div>
                  <label className="font-mono text-ivory/80 block mb-1">Select File</label>
                  <input
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    className="w-full p-2 rounded-xl bg-black/40 border border-ivory/15 font-mono text-xs text-ivory"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="btn-oxblood w-full py-2.5 rounded-xl font-display font-semibold text-xs flex items-center justify-center gap-2 mt-4"
                >
                  <Upload className="w-4 h-4" />
                  <span>{uploading ? "Uploading to Cloud..." : "Upload File"}</span>
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

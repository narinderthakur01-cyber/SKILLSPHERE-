import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, FileText, CheckCircle2, AlertTriangle, AlertCircle,
  X, RefreshCw, Check, Trash2, ArrowLeft, HelpCircle, Layers,
  FileSpreadsheet, Image as ImageIcon, Sparkles, Database, Plus
} from 'lucide-react';
import { questionBankAPI } from '../services/api';
import { GlassModal, useToast } from './MotionComponents';

export const InlineQuestionUploadModal = ({
  isOpen,
  onClose,
  technologyHint = 'Python',
  topicHint = '',
  onSuccess
}) => {
  const { addToast } = useToast();
  const fileInputRef = useRef(null);

  // Workflow Step: 'UPLOAD' | 'PREVIEW'
  const [step, setStep] = useState('UPLOAD');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [importing, setImporting] = useState(false);

  // Extracted Data
  const [extractedMeta, setExtractedMeta] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [activeFilter, setActiveFilter] = useState('ALL'); // 'ALL' | 'READY' | 'NEEDS_KEY' | 'DUPLICATES'
  const [searchTerm, setSearchTerm] = useState('');

  // Reset state when closing
  const handleClose = () => {
    setStep('UPLOAD');
    setExtractedMeta(null);
    setQuestions([]);
    setActiveFilter('ALL');
    setSearchTerm('');
    onClose();
  };

  // --------------------------------------------------------------------------
  // File Upload & Extraction Handler
  // --------------------------------------------------------------------------
  const handleFileSelect = async (file) => {
    if (!file) return;

    // Validate size (15MB)
    if (file.size > 15 * 1024 * 1024) {
      addToast('File size exceeds the 15MB limit.', 'error');
      return;
    }

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('technology', technologyHint || 'Python');
      if (topicHint) {
        formData.append('topic', topicHint);
      }

      const res = await questionBankAPI.uploadAndExtract(formData);
      const data = res.data;

      setExtractedMeta({
        filename: data.filename,
        file_type: data.file_type,
        file_size: file.size,
        is_scanned: data.is_scanned,
        total_extracted: data.total_extracted,
        valid_count: data.valid_count,
        missing_answer_count: data.missing_answer_count,
        duplicate_count: data.duplicate_count
      });

      // Initialize question list with selection flags
      const formatted = (data.questions || []).map((q) => ({
        ...q,
        is_selected: q.validation_status === 'VALID' || q.validation_status === 'MISSING_ANSWER'
      }));

      setQuestions(formatted);
      setStep('PREVIEW');

      if (data.total_extracted === 0) {
        addToast('No multiple-choice questions could be detected in this file.', 'warning');
      } else {
        addToast(`Extracted ${data.total_extracted} question(s)! Review and approve below.`, 'success');
      }
    } catch (err) {
      console.error('File extraction failed:', err);
      addToast(err.response?.data?.detail || 'Failed to extract questions from file.', 'error');
    } finally {
      setUploading(false);
    }
  };

  // Drag & drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // --------------------------------------------------------------------------
  // Question Editing Helpers
  // --------------------------------------------------------------------------
  const handleUpdateQuestion = (qIndex, field, value) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const target = { ...updated[qIndex], [field]: value };

      // Re-evaluate validation status if prompt or options change
      if (field === 'question_text' && value.trim().length >= 5 && target.validation_status === 'INVALID_OPTIONS') {
        const hasKey = target.options.some((o) => o.is_correct);
        target.validation_status = hasKey ? 'VALID' : 'MISSING_ANSWER';
      }

      updated[qIndex] = target;
      return updated;
    });
  };

  const handleSetCorrectOption = (qIndex, optionKey) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const target = { ...updated[qIndex] };
      target.options = target.options.map((opt) => ({
        ...opt,
        is_correct: opt.option_key === optionKey
      }));
      target.correct_option = optionKey;
      target.has_correct_answer = true;

      // Update validation status if previously missing answer key
      if (target.validation_status === 'MISSING_ANSWER') {
        target.validation_status = 'VALID';
      }

      updated[qIndex] = target;
      return updated;
    });
  };

  const handleUpdateOptionText = (qIndex, optKey, newText) => {
    setQuestions((prev) => {
      const updated = [...prev];
      const target = { ...updated[qIndex] };
      target.options = target.options.map((opt) =>
        opt.option_key === optKey ? { ...opt, option_text: newText } : opt
      );
      updated[qIndex] = target;
      return updated;
    });
  };

  const handleRemoveQuestion = (qIndex) => {
    setQuestions((prev) => prev.filter((_, idx) => idx !== qIndex));
    addToast('Question removed from import preview.', 'info');
  };

  const handleToggleSelectAll = (select) => {
    setQuestions((prev) =>
      prev.map((q) => {
        if (q.validation_status === 'EXACT_DUPLICATE') return { ...q, is_selected: false };
        return { ...q, is_selected: select };
      })
    );
  };

  // --------------------------------------------------------------------------
  // Batch Import Execution
  // --------------------------------------------------------------------------
  const handleCommitImport = async () => {
    const selectedQuestions = questions.filter((q) => q.is_selected);

    if (selectedQuestions.length === 0) {
      addToast('Please select at least one question to import.', 'warning');
      return;
    }

    // Check for questions with missing answer keys among selected
    const unverified = selectedQuestions.filter((q) => !q.options.some((o) => o.is_correct));
    if (unverified.length > 0) {
      addToast(`Please assign a correct answer to all selected questions (${unverified.length} unassigned).`, 'error');
      return;
    }

    try {
      setImporting(true);
      const payload = {
        filename: extractedMeta?.filename || 'imported_questions.pdf',
        file_type: extractedMeta?.file_type || 'PDF',
        file_size: extractedMeta?.file_size || 0,
        technology: technologyHint || 'Python',
        topic: topicHint || 'General',
        questions: selectedQuestions.map((q) => ({
          question_text: q.question_text.trim(),
          options: q.options.map((o) => ({
            option_key: o.option_key,
            option_text: o.option_text.trim(),
            is_correct: Boolean(o.is_correct)
          })),
          difficulty: q.difficulty || 'INTERMEDIATE',
          marks: q.marks || 1,
          explanation: q.explanation || null,
          technology: q.technology || technologyHint || 'General',
          topic: q.topic || topicHint || 'General',
          source_file: extractedMeta?.filename,
          source_page: q.source_page || 1,
          is_approved: true
        }))
      };

      const res = await questionBankAPI.batchImport(payload);
      addToast(res.data?.message || `Successfully imported ${selectedQuestions.length} questions into Question Bank!`, 'success');

      // Trigger parent callback to refresh availability and return to builder
      if (onSuccess) {
        onSuccess(res.data);
      }
      handleClose();
    } catch (err) {
      console.error('Batch import failed:', err);
      addToast(err.response?.data?.detail || 'Failed to save questions to Question Bank.', 'error');
    } finally {
      setImporting(false);
    }
  };

  // --------------------------------------------------------------------------
  // Filtered Questions Computation
  // --------------------------------------------------------------------------
  const filteredQuestions = questions.filter((q) => {
    if (activeFilter === 'READY') {
      if (q.validation_status !== 'VALID') return false;
    } else if (activeFilter === 'NEEDS_KEY') {
      if (q.validation_status !== 'MISSING_ANSWER') return false;
    } else if (activeFilter === 'DUPLICATES') {
      if (!['EXACT_DUPLICATE', 'SIMILAR_DUPLICATE'].includes(q.validation_status)) return false;
    }

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      const inText = q.question_text.toLowerCase().includes(term);
      const inOpts = q.options.some((o) => o.option_text.toLowerCase().includes(term));
      if (!inText && !inOpts) return false;
    }

    return true;
  });

  const selectedCount = questions.filter((q) => q.is_selected).length;
  const readyCount = questions.filter((q) => q.validation_status === 'VALID').length;
  const needsKeyCount = questions.filter((q) => q.validation_status === 'MISSING_ANSWER').length;
  const dupCount = questions.filter((q) => ['EXACT_DUPLICATE', 'SIMILAR_DUPLICATE'].includes(q.validation_status)).length;

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={handleClose}
      title={step === 'UPLOAD' ? 'Upload Questions to Question Bank' : `Import Preview: ${extractedMeta?.filename || 'Extracted Questions'}`}
      subtitle={
        step === 'UPLOAD'
          ? `Upload technical question files directly into ${technologyHint || 'your target technology'} question bank`
          : `Review extracted MCQs, set missing answer keys, and approve questions for immediate assessment generation`
      }
    >
      <div className="font-mono text-xs text-charcoal dark:text-ivory space-y-5 max-h-[78vh] overflow-y-auto pr-1">
        {step === 'UPLOAD' ? (
          /* ================================================================= */
          /* STEP 1: FILE DROPZONE & FORMAT GUIDE */
          /* ================================================================= */
          <div className="space-y-5">
            {/* Target Tech & Topic Banner */}
            <div className="p-3.5 rounded-2xl bg-oxblood/10 border border-oxblood/20 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-oxblood dark:text-rose" />
                <span className="text-xs font-bold text-oxblood dark:text-rose">
                  Target Tech: {technologyHint} {topicHint ? `\u2022 Topic: ${topicHint}` : ''}
                </span>
              </div>
              <span className="text-[10px] text-slate/50 dark:text-ivory/50">
                Extracted questions will be classified here
              </span>
            </div>

            {/* Dropzone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`p-8 sm:p-12 border-2 border-dashed rounded-3xl text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-4 ${
                isDragging
                  ? 'border-oxblood bg-oxblood/10 scale-[1.01]'
                  : 'border-slate/20 dark:border-white/10 hover:border-oxblood/50 bg-slate/5 dark:bg-white/5'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.xlsx,.xls,.csv,.txt,.jpg,.jpeg,.png"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
                }}
              />

              {uploading ? (
                <div className="py-6 flex flex-col items-center gap-3">
                  <RefreshCw className="w-8 h-8 animate-spin text-oxblood dark:text-rose" />
                  <p className="font-bold text-sm">Processing & Extracting MCQs...</p>
                  <p className="text-[11px] text-slate/50">Running digital extraction, OCR and structure analysis</p>
                </div>
              ) : (
                <>
                  <div className="w-16 h-16 rounded-2xl bg-oxblood/10 flex items-center justify-center text-oxblood dark:text-rose">
                    <Upload className="w-8 h-8" />
                  </div>
                  <div className="space-y-1">
                    <p className="font-bold text-sm">
                      Drag & Drop your question file here, or <span className="text-oxblood dark:text-rose underline">Browse</span>
                    </p>
                    <p className="text-[11px] text-slate/50">
                      Supports PDF (digital & scanned OCR), Word (DOCX), Excel (XLSX), CSV, TXT, and Images (JPG, PNG) up to 15MB
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* Supported Formats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-2">
              <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 space-y-1">
                <span className="flex items-center gap-1.5 font-bold text-oxblood dark:text-rose text-[11px]">
                  <FileText size={13} /> PDF Documents
                </span>
                <p className="text-[10px] text-slate/50 leading-snug">Digital text & OCR fallback for scanned exam sheets.</p>
              </div>

              <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 space-y-1">
                <span className="flex items-center gap-1.5 font-bold text-oxblood dark:text-rose text-[11px]">
                  <FileSpreadsheet size={13} /> Excel & CSV
                </span>
                <p className="text-[10px] text-slate/50 leading-snug">Tabular spreadsheets with question, options & answers.</p>
              </div>

              <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/15 space-y-1">
                <span className="flex items-center gap-1.5 font-bold text-oxblood dark:text-rose text-[11px]">
                  <ImageIcon size={13} /> Photos & Scans
                </span>
                <p className="text-[10px] text-slate/50 leading-snug">JPG/PNG images preprocessed via high-accuracy Tesseract OCR.</p>
              </div>
            </div>

            {/* Cancel Button */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleClose}
                className="px-5 py-2.5 rounded-xl bg-slate/10 hover:bg-slate/15 text-xs font-mono uppercase tracking-wider min-h-[40px]"
              >
                Cancel & Return
              </button>
            </div>
          </div>
        ) : (
          /* ================================================================= */
          /* STEP 2: INTERACTIVE PREVIEW, VALIDATION & APPROVAL */
          /* ================================================================= */
          <div className="space-y-4">
            {/* Header Telemetry Pills */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-charcoal dark:text-ivory">
                  Extracted: <strong>{questions.length}</strong> MCQs
                </span>
                {extractedMeta?.is_scanned && (
                  <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 text-[10px] font-bold border border-amber-500/20">
                    OCR Scanned
                  </span>
                )}
              </div>

              <div className="flex flex-wrap gap-1.5 text-[10px]">
                <button
                  type="button"
                  onClick={() => setActiveFilter('ALL')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    activeFilter === 'ALL'
                      ? 'bg-oxblood text-ivory font-bold'
                      : 'bg-white/5 text-slate/60 hover:bg-white/10'
                  }`}
                >
                  All ({questions.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveFilter('READY')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    activeFilter === 'READY'
                      ? 'bg-emerald-600 text-ivory font-bold'
                      : 'bg-white/5 text-emerald-500 hover:bg-white/10'
                  }`}
                >
                  Ready ({readyCount})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveFilter('NEEDS_KEY')}
                  className={`px-2.5 py-1 rounded-lg transition ${
                    activeFilter === 'NEEDS_KEY'
                      ? 'bg-amber-600 text-ivory font-bold'
                      : 'bg-white/5 text-amber-500 hover:bg-white/10'
                  }`}
                >
                  Needs Key ({needsKeyCount})
                </button>
                {dupCount > 0 && (
                  <button
                    type="button"
                    onClick={() => setActiveFilter('DUPLICATES')}
                    className={`px-2.5 py-1 rounded-lg transition ${
                      activeFilter === 'DUPLICATES'
                        ? 'bg-rose-600 text-ivory font-bold'
                        : 'bg-white/5 text-rose-500 hover:bg-white/10'
                    }`}
                  >
                    Duplicates ({dupCount})
                  </button>
                )}
              </div>
            </div>

            {/* Search & Bulk Selection Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
              <input
                type="text"
                placeholder="Search extracted questions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full sm:w-64 bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-1.5 text-xs min-h-[36px]"
              />

              <div className="flex items-center gap-2 text-[11px] ml-auto">
                <button
                  type="button"
                  onClick={() => handleToggleSelectAll(true)}
                  className="px-2.5 py-1 rounded-lg bg-slate/10 hover:bg-slate/15 transition text-oxblood dark:text-rose font-bold"
                >
                  Select All Approved
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleSelectAll(false)}
                  className="px-2.5 py-1 rounded-lg bg-slate/10 hover:bg-slate/15 transition text-slate/50"
                >
                  Deselect All
                </button>
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-3 max-h-[46vh] overflow-y-auto pr-1">
              {filteredQuestions.length === 0 ? (
                <div className="p-8 text-center rounded-2xl bg-slate/5 text-slate/50">
                  No questions match the current filter.
                </div>
              ) : (
                filteredQuestions.map((q, idx) => {
                  const originalIndex = questions.findIndex((orig) => orig.temp_id === q.temp_id);
                  const isReady = q.validation_status === 'VALID';
                  const isMissingKey = q.validation_status === 'MISSING_ANSWER';
                  const isDuplicate = ['EXACT_DUPLICATE', 'SIMILAR_DUPLICATE'].includes(q.validation_status);

                  return (
                    <div
                      key={q.temp_id || idx}
                      className={`p-4 rounded-2xl border transition-all space-y-3 ${
                        q.is_selected
                          ? 'bg-slate/5 dark:bg-white/5 border-oxblood/40'
                          : 'bg-slate/5/50 dark:bg-white/5/50 border-slate/10 opacity-75'
                      }`}
                    >
                      {/* Top Bar: Select Checkbox, Badges, Remove */}
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={q.is_selected || false}
                            onChange={(e) => handleUpdateQuestion(originalIndex, 'is_selected', e.target.checked)}
                            className="w-4 h-4 text-oxblood rounded cursor-pointer"
                          />
                          <span className="font-bold text-xs">
                            #{q.row_index || idx + 1}
                          </span>
                          {q.source_page && (
                            <span className="px-2 py-0.5 rounded bg-slate/10 text-[10px] text-slate/50">
                              Page/Row {q.source_page}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          {isReady && (
                            <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-500/20 flex items-center gap-1">
                              <CheckCircle2 size={11} /> Ready
                            </span>
                          )}
                          {isMissingKey && (
                            <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 text-[10px] font-bold border border-amber-500/20 flex items-center gap-1">
                              <AlertCircle size={11} /> Missing Answer Key
                            </span>
                          )}
                          {isDuplicate && (
                            <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-600 dark:text-rose-400 text-[10px] font-bold border border-rose-500/20 flex items-center gap-1">
                              <AlertTriangle size={11} /> {q.validation_status === 'EXACT_DUPLICATE' ? 'Exact Duplicate' : 'Similar Duplicate'}
                            </span>
                          )}

                          <button
                            type="button"
                            onClick={() => handleRemoveQuestion(originalIndex)}
                            className="p-1 text-slate/40 hover:text-rose transition"
                            title="Discard question"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>

                      {/* Duplicate Warning notice if applicable */}
                      {q.similarity_reason && (
                        <p className="text-[11px] text-rose font-sans font-bold bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
                          {q.similarity_reason}
                        </p>
                      )}

                      {/* Question Prompt */}
                      <div>
                        <input
                          type="text"
                          value={q.question_text}
                          onChange={(e) => handleUpdateQuestion(originalIndex, 'question_text', e.target.value)}
                          placeholder="Question prompt..."
                          className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-xl p-2.5 text-xs font-sans font-medium"
                        />
                      </div>

                      {/* Options List with Radio to select correct key */}
                      <div className="space-y-1.5 pl-2 border-l-2 border-oxblood/30">
                        <div className="flex justify-between items-center text-[10px] text-slate/50 mb-1">
                          <span>Options (Select the correct answer):</span>
                          {isMissingKey && (
                            <span className="text-amber-500 font-bold">Please select an answer</span>
                          )}
                        </div>

                        {q.options.map((opt) => (
                          <div key={opt.option_key} className="flex items-center gap-2">
                            <input
                              type="radio"
                              name={`corr_${q.temp_id || originalIndex}`}
                              checked={Boolean(opt.is_correct)}
                              onChange={() => handleSetCorrectOption(originalIndex, opt.option_key)}
                              className="w-3.5 h-3.5 text-oxblood cursor-pointer"
                            />
                            <span className="w-5 text-center font-bold text-oxblood dark:text-rose">
                              {opt.option_key})
                            </span>
                            <input
                              type="text"
                              value={opt.option_text}
                              onChange={(e) => handleUpdateOptionText(originalIndex, opt.option_key, e.target.value)}
                              className="flex-1 bg-white/10 dark:bg-charcoal border border-slate/15 rounded-lg px-2.5 py-1 text-xs font-sans"
                            />
                          </div>
                        ))}
                      </div>

                      {/* Metadata Row: Difficulty, Marks, Explanation */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-[11px]">
                        <div>
                          <label className="block text-[9px] uppercase text-slate/50">Difficulty:</label>
                          <select
                            value={q.difficulty || 'INTERMEDIATE'}
                            onChange={(e) => handleUpdateQuestion(originalIndex, 'difficulty', e.target.value)}
                            className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-lg px-2 py-1 text-xs"
                          >
                            <option value="BEGINNER">Beginner</option>
                            <option value="INTERMEDIATE">Intermediate</option>
                            <option value="ADVANCED">Advanced</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-[9px] uppercase text-slate/50">Marks:</label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={q.marks || 1}
                            onChange={(e) => handleUpdateQuestion(originalIndex, 'marks', parseInt(e.target.value, 10) || 1)}
                            className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-lg px-2 py-1 text-xs text-center"
                          />
                        </div>

                        <div>
                          <label className="block text-[9px] uppercase text-slate/50">Explanation (Optional):</label>
                          <input
                            type="text"
                            value={q.explanation || ''}
                            onChange={(e) => handleUpdateQuestion(originalIndex, 'explanation', e.target.value)}
                            placeholder="Explanation rationale..."
                            className="w-full bg-white/10 dark:bg-charcoal border border-slate/20 rounded-lg px-2 py-1 text-xs font-sans"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Bottom Actions Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate/15">
              <div className="flex items-center gap-2 text-xs">
                <span>
                  Selected for Bank: <strong className="text-oxblood dark:text-rose">{selectedCount}</strong> / {questions.length}
                </span>
                {needsKeyCount > 0 && (
                  <span className="text-[10px] text-amber-500 font-bold">
                    ({needsKeyCount} missing answer key)
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                <button
                  type="button"
                  onClick={() => setStep('UPLOAD')}
                  className="px-4 py-2 rounded-xl bg-slate/10 hover:bg-slate/15 text-xs font-mono uppercase tracking-wider min-h-[40px]"
                >
                  <ArrowLeft size={13} className="inline mr-1" /> Re-upload
                </button>

                <button
                  type="button"
                  onClick={handleCommitImport}
                  disabled={importing || selectedCount === 0}
                  className="px-5 py-2 rounded-xl bg-oxblood text-ivory hover:bg-oxblood/90 text-xs font-mono font-bold uppercase tracking-wider min-h-[40px] disabled:opacity-40 flex items-center gap-1.5 shadow-md"
                >
                  {importing ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Saving to Bank...
                    </>
                  ) : (
                    <>
                      <Database size={14} />
                      Approve & Import ({selectedCount})
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </GlassModal>
  );
};

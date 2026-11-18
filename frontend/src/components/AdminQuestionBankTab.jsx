import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Plus, Search, Filter, Upload, Download, CheckCircle2,
  XCircle, AlertCircle, Edit3, Archive, RefreshCw, Eye, Sparkles,
  Layers, FileText, Check, X, ShieldAlert, Award, Tag
} from 'lucide-react';
import { questionBankAPI } from '../services/api';
import { GlassModal, useToast, AnimatedCounter } from './MotionComponents';

export const AdminQuestionBankTab = () => {
  const { addToast } = useToast();

  const [subTab, setSubTab] = useState('browse'); // 'browse' | 'bulk_import'
  const [questions, setQuestions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [technologies, setTechnologies] = useState([]);

  // Filter States
  const [search, setSearch] = useState('');
  const [selectedTech, setSelectedTech] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [statusFilter, setStatusFilter] = useState('ACTIVE');
  const [page, setPage] = useState(1);
  const limit = 25;

  // Add/Edit Question Modal State
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [modalFormData, setModalFormData] = useState({
    technology: '',
    topic: '',
    subtopic: '',
    difficulty: 'INTERMEDIATE',
    marks: 5,
    question_text: '',
    explanation: '',
    tags: '',
    options: [
      { option_key: 'A', option_text: '', is_correct: true },
      { option_key: 'B', option_text: '', is_correct: false },
      { option_key: 'C', option_text: '', is_correct: false },
      { option_key: 'D', option_text: '', is_correct: false },
    ]
  });
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [savingQuestion, setSavingQuestion] = useState(false);

  // Bulk Import State
  const [csvContent, setCsvContent] = useState('');
  const [importPreview, setImportPreview] = useState(null);
  const [validatingCsv, setValidatingCsv] = useState(false);
  const [committingCsv, setCommittingCsv] = useState(false);

  // Fetch Questions
  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const params = {
        technology: selectedTech || null,
        difficulty: selectedDifficulty || null,
        search: search.trim() || null,
        status: statusFilter,
        page,
        limit
      };
      const res = await questionBankAPI.list(params);
      setQuestions(res.data.items || []);
      setTotalCount(res.data.total || 0);
    } catch (err) {
      console.error('Failed to load question bank:', err);
      addToast('Failed to load questions from repository.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch Technologies Metadata
  const fetchTechnologies = async () => {
    try {
      const res = await questionBankAPI.getTechnologies();
      setTechnologies(res.data.technologies || []);
    } catch (err) {
      console.error('Failed to load technologies:', err);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [selectedTech, selectedDifficulty, statusFilter, page]);

  useEffect(() => {
    fetchTechnologies();
  }, []);

  // Search with debounce
  useEffect(() => {
    const handler = setTimeout(() => {
      setPage(1);
      fetchQuestions();
    }, 350);
    return () => clearTimeout(handler);
  }, [search]);

  // Open Create Modal
  const handleOpenCreateModal = () => {
    setEditingQuestion(null);
    setDuplicateWarning(null);
    setModalFormData({
      technology: technologies[0]?.technology || 'Python',
      topic: '',
      subtopic: '',
      difficulty: 'INTERMEDIATE',
      marks: 5,
      question_text: '',
      explanation: '',
      tags: '',
      options: [
        { option_key: 'A', option_text: '', is_correct: true },
        { option_key: 'B', option_text: '', is_correct: false },
        { option_key: 'C', option_text: '', is_correct: false },
        { option_key: 'D', option_text: '', is_correct: false },
      ]
    });
    setShowQuestionModal(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (q) => {
    setEditingQuestion(q);
    setDuplicateWarning(null);
    setModalFormData({
      technology: q.technology,
      topic: q.topic,
      subtopic: q.subtopic || '',
      difficulty: q.difficulty,
      marks: q.marks,
      question_text: q.question_text,
      explanation: q.explanation || '',
      tags: (q.tags || []).join(', '),
      options: q.options.map((o) => ({
        option_key: o.option_key,
        option_text: o.option_text,
        is_correct: o.is_correct || false
      }))
    });
    setShowQuestionModal(true);
  };

  // Duplicate Check on Question Text blur
  const handleCheckDuplicate = async () => {
    if (!modalFormData.question_text.trim() || modalFormData.question_text.length < 5) return;
    try {
      const res = await questionBankAPI.checkDuplicate(
        modalFormData.question_text,
        editingQuestion?.id || null
      );
      if (res.data.is_duplicate) {
        setDuplicateWarning(res.data.similarity_reason || 'An identical question already exists.');
      } else {
        setDuplicateWarning(null);
      }
    } catch (err) {
      console.error('Duplicate check error:', err);
    }
  };

  // Save Question (Create or Edit)
  const handleSaveQuestion = async (e) => {
    e.preventDefault();
    if (!modalFormData.options.some((o) => o.is_correct)) {
      addToast('Exactly one option must be marked as correct.', 'error');
      return;
    }
    try {
      setSavingQuestion(true);
      const payload = {
        technology: modalFormData.technology.trim(),
        topic: modalFormData.topic.trim(),
        subtopic: modalFormData.subtopic.trim() || null,
        difficulty: modalFormData.difficulty,
        marks: parseInt(modalFormData.marks, 10) || 5,
        question_text: modalFormData.question_text.trim(),
        explanation: modalFormData.explanation.trim() || null,
        tags: modalFormData.tags.split(',').map((t) => t.trim()).filter(Boolean),
        options: modalFormData.options
      };

      if (editingQuestion) {
        await questionBankAPI.update(editingQuestion.id, payload);
        addToast('Question updated successfully.', 'success');
      } else {
        await questionBankAPI.create(payload);
        addToast('Global question created successfully.', 'success');
      }

      setShowQuestionModal(false);
      fetchQuestions();
      fetchTechnologies();
    } catch (err) {
      console.error('Failed to save question:', err);
      addToast(err.response?.data?.detail || 'Failed to save question.', 'error');
    } finally {
      setSavingQuestion(false);
    }
  };

  // Archive Question
  const handleArchiveQuestion = async (questionId) => {
    if (!window.confirm('Are you sure you want to archive this question? It will not be sampled for new assessments.')) return;
    try {
      await questionBankAPI.archive(questionId);
      addToast('Question archived.', 'success');
      fetchQuestions();
    } catch (err) {
      console.error('Failed to archive question:', err);
      addToast('Failed to archive question.', 'error');
    }
  };

  // CSV Template Download
  const handleDownloadTemplate = () => {
    const templateContent = `technology,topic,subtopic,difficulty,question_text,explanation,marks,option_a,option_b,option_c,option_d,correct_option,tags
Python,Core,Iterators,BEGINNER,Which keyword creates a generator in Python?,The yield statement pauses execution and yields values on demand.,5,return,yield,generate,async,B,python,core,generators
JavaScript,Async,Promises,INTERMEDIATE,What does Promise.all() do when one promise rejects?,Promise.all rejects immediately with the error of the first rejected promise.,5,Waits for all to finish,Rejects immediately,Resolves with undefined,Retries the promise,B,javascript,async,promises
SQL,Indexing,B-Tree,ADVANCED,What is the typical time complexity of an indexed lookup in a B-Tree?,B-Tree search complexity is logarithmic with respect to rows.,5,O(1),O(log n),O(n),O(n log n),B,sql,indexing,database
`;
    const blob = new Blob([templateContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'skillsphere_question_bank_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle CSV File Upload
  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setCsvContent(event.target?.result || '');
      setImportPreview(null);
    };
    reader.readAsText(file);
  };

  // Validate CSV
  const handleValidateCsv = async () => {
    if (!csvContent.trim()) {
      addToast('Please enter or upload CSV content to validate.', 'error');
      return;
    }
    try {
      setValidatingCsv(true);
      const res = await questionBankAPI.bulkImport(csvContent, false);
      setImportPreview(res.data);
      if (res.data.invalid_rows_count > 0) {
        addToast(`Validation complete: ${res.data.valid_rows_count} valid, ${res.data.invalid_rows_count} invalid.`, 'info');
      } else {
        addToast(`All ${res.data.valid_rows_count} rows passed validation! Ready to import.`, 'success');
      }
    } catch (err) {
      console.error('Validation error:', err);
      addToast(err.response?.data?.detail || 'CSV validation failed.', 'error');
    } finally {
      setValidatingCsv(false);
    }
  };

  // Commit CSV Import
  const handleCommitCsv = async () => {
    if (!importPreview || !importPreview.can_commit) return;
    try {
      setCommittingCsv(true);
      const res = await questionBankAPI.bulkImport(csvContent, true);
      addToast(`Successfully imported ${res.data.valid_rows_count} questions into the bank!`, 'success');
      setCsvContent('');
      setImportPreview(null);
      setSubTab('browse');
      fetchQuestions();
      fetchTechnologies();
    } catch (err) {
      console.error('Commit error:', err);
      addToast(err.response?.data?.detail || 'Failed to commit CSV questions.', 'error');
    } finally {
      setCommittingCsv(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Sub-tab navigation */}
      <div className="flex items-center justify-between border-b border-slate/15 dark:border-rose/15 pb-2">
        <div className="flex gap-2">
          <button
            onClick={() => setSubTab('browse')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase tracking-wider transition-colors min-h-[40px] flex items-center gap-2 ${
              subTab === 'browse'
                ? 'bg-oxblood text-ivory shadow-sm'
                : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
            }`}
          >
            <Database size={15} /> Question Repository ({totalCount})
          </button>
          <button
            onClick={() => setSubTab('bulk_import')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase tracking-wider transition-colors min-h-[40px] flex items-center gap-2 ${
              subTab === 'bulk_import'
                ? 'bg-oxblood text-ivory shadow-sm'
                : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory'
            }`}
          >
            <Upload size={15} /> Bulk CSV Import
          </button>
        </div>

        {subTab === 'browse' && (
          <button
            onClick={handleOpenCreateModal}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase tracking-wider shadow-sm min-h-[40px]"
          >
            <Plus size={15} /> Add Global Question
          </button>
        )}
      </div>

      {/* ==================================================================== */}
      {/* SUB-TAB 1: QUESTION REPOSITORY BROWSER */}
      {/* ==================================================================== */}
      {subTab === 'browse' && (
        <div className="space-y-6">
          {/* Filter Bar */}
          <div className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-sm space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate/40 dark:text-ivory/40 w-4 h-4" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search question text or tags..."
                  className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 text-xs font-sans text-charcoal dark:text-ivory placeholder:text-slate/40 min-h-[40px]"
                />
              </div>

              {/* Technology Filter */}
              <select
                value={selectedTech}
                onChange={(e) => {
                  setSelectedTech(e.target.value);
                  setPage(1);
                }}
                className="bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-charcoal dark:text-ivory min-h-[40px]"
              >
                <option value="">All Technologies ({technologies.length})</option>
                {technologies.map((t) => (
                  <option key={t.technology} value={t.technology} className="bg-charcoal text-ivory">
                    {t.technology} ({t.total_questions})
                  </option>
                ))}
              </select>

              {/* Difficulty Filter */}
              <select
                value={selectedDifficulty}
                onChange={(e) => {
                  setSelectedDifficulty(e.target.value);
                  setPage(1);
                }}
                className="bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-charcoal dark:text-ivory min-h-[40px]"
              >
                <option value="">All Difficulties</option>
                <option value="BEGINNER" className="bg-charcoal text-ivory">Beginner</option>
                <option value="INTERMEDIATE" className="bg-charcoal text-ivory">Intermediate</option>
                <option value="ADVANCED" className="bg-charcoal text-ivory">Advanced</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono text-charcoal dark:text-ivory min-h-[40px]"
              >
                <option value="ACTIVE" className="bg-charcoal text-ivory">Active Only</option>
                <option value="ARCHIVED" className="bg-charcoal text-ivory">Archived Only</option>
                <option value="ALL" className="bg-charcoal text-ivory">All Statuses</option>
              </select>
            </div>
          </div>

          {/* Question List */}
          {loading ? (
            <div className="py-12 flex items-center justify-center font-mono text-xs text-slate/60 dark:text-ivory/50">
              <RefreshCw className="w-5 h-5 animate-spin mr-2 text-oxblood" /> Loading questions...
            </div>
          ) : questions.length === 0 ? (
            <div className="p-12 text-center rounded-2xl border border-dashed border-slate/20 dark:border-white/10 font-mono text-xs text-slate/50 dark:text-ivory/40">
              No questions found matching your filter criteria.
            </div>
          ) : (
            <div className="space-y-4">
              {questions.map((q) => (
                <div
                  key={q.id}
                  className="glass-card p-5 rounded-2xl border border-slate/15 dark:border-rose/15 shadow-sm space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-md bg-oxblood/10 text-oxblood dark:text-rose text-[11px] font-mono font-bold uppercase tracking-wider border border-oxblood/20">
                        {q.technology}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-md bg-slate/10 dark:bg-white/10 text-slate/70 dark:text-ivory/60 text-[11px] font-mono">
                        {q.topic}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider ${
                        q.difficulty === 'BEGINNER'
                          ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                          : q.difficulty === 'INTERMEDIATE'
                          ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                          : 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/20'
                      }`}>
                        {q.difficulty}
                      </span>
                      <span className="text-[11px] font-mono text-slate/50 dark:text-ivory/40">
                        {q.marks} Marks
                      </span>
                      {q.is_global ? (
                        <span className="px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-500 border border-blue-500/20 text-[10px] font-mono font-bold uppercase">
                          Global Standard
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-slate/10 text-slate/60 text-[10px] font-mono">
                          Custom ({q.creator_name || 'Recruiter'})
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className="text-slate/50 dark:text-ivory/40">
                        Used in <strong className="text-charcoal dark:text-ivory">{q.usage_count}</strong> assessment(s)
                      </span>
                      <button
                        onClick={() => handleOpenEditModal(q)}
                        className="p-1.5 rounded-lg bg-slate/5 dark:bg-white/5 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory transition-colors"
                        title="Edit Question"
                      >
                        <Edit3 size={14} />
                      </button>
                      {q.status === 'ACTIVE' && (
                        <button
                          onClick={() => handleArchiveQuestion(q.id)}
                          className="p-1.5 rounded-lg bg-slate/5 dark:bg-white/5 hover:bg-rose/20 text-rose transition-colors"
                          title="Archive Question"
                        >
                          <Archive size={14} />
                        </button>
                      )}
                    </div>
                  </div>

                  <p className="font-sans text-sm font-semibold text-charcoal dark:text-ivory">
                    {q.question_text}
                  </p>

                  {/* Options List */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {q.options.map((opt) => (
                      <div
                        key={opt.id}
                        className={`p-2.5 rounded-xl border text-xs font-sans flex items-center justify-between ${
                          opt.is_correct
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-300 font-medium'
                            : 'bg-slate/5 dark:bg-white/5 border-slate/10 dark:border-white/5 text-slate/80 dark:text-ivory/70'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-black/10 dark:bg-white/10 font-mono text-[10px] flex items-center justify-center font-bold">
                            {opt.option_key}
                          </span>
                          <span>{opt.option_text}</span>
                        </span>
                        {opt.is_correct && (
                          <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-bold uppercase">
                            <CheckCircle2 size={13} /> Correct
                          </span>
                        )}
                      </div>
                    ))}
                  </div>

                  {q.explanation && (
                    <div className="p-3 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 dark:border-white/5 text-[11px] font-sans text-slate/70 dark:text-ivory/60">
                      <strong className="font-mono text-oxblood dark:text-rose mr-1">Explanation:</strong>
                      {q.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* SUB-TAB 2: BULK CSV IMPORT */}
      {/* ==================================================================== */}
      {subTab === 'bulk_import' && (
        <div className="space-y-6">
          <div className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-slate/15 dark:border-rose/15">
              <div>
                <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory">
                  Bulk MCQ Question Importer
                </h3>
                <p className="text-xs font-mono text-slate/60 dark:text-ivory/60 mt-0.5">
                  Import hundreds of technical questions at once. System validates format, prevents duplicates, and checks options.
                </p>
              </div>

              <button
                onClick={handleDownloadTemplate}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory text-xs font-mono font-bold uppercase tracking-wider min-h-[40px]"
              >
                <Download size={15} /> Download CSV Template
              </button>
            </div>

            {/* Upload or Paste */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono font-bold uppercase text-slate/70 dark:text-ivory/60">
                  CSV Data Payload (Upload File or Paste Raw Text)
                </label>
                <label className="cursor-pointer text-xs font-mono text-oxblood dark:text-rose hover:underline flex items-center gap-1">
                  <Upload size={13} /> Upload .CSV file
                  <input type="file" accept=".csv" onChange={handleFileUpload} className="hidden" />
                </label>
              </div>

              <textarea
                rows={8}
                value={csvContent}
                onChange={(e) => {
                  setCsvContent(e.target.value);
                  setImportPreview(null);
                }}
                placeholder="technology,topic,subtopic,difficulty,question_text,explanation,marks,option_a,option_b,option_c,option_d,correct_option,tags&#10;Python,Core,,INTERMEDIATE,What does GIL do?,Prevents multi-threading bytecodes.,5,A,B,C,D,A,python,concurrency"
                className="w-full font-mono text-xs bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-2xl p-4 text-charcoal dark:text-ivory placeholder:text-slate/40 focus:outline-none focus:border-oxblood/50"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={handleValidateCsv}
                disabled={validatingCsv || !csvContent.trim()}
                className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 dark:hover:bg-white/15 text-charcoal dark:text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-2 min-h-[42px]"
              >
                {validatingCsv ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Eye size={15} />}
                Validate CSV Format
              </button>

              {importPreview && importPreview.can_commit && (
                <button
                  onClick={handleCommitCsv}
                  disabled={committingCsv}
                  className="px-5 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-2 min-h-[42px] shadow-sm shadow-oxblood/20"
                >
                  {committingCsv ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 size={15} />}
                  Commit {importPreview.valid_rows_count} Valid Questions
                </button>
              )}
            </div>
          </div>

          {/* Validation Preview Results */}
          {importPreview && (
            <div className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-sm space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate/10 dark:border-white/5">
                <div className="flex items-center gap-3">
                  <h4 className="font-display text-base font-bold text-charcoal dark:text-ivory">
                    Validation Results
                  </h4>
                  <span className="px-2.5 py-0.5 rounded-full bg-slate/10 text-xs font-mono text-slate/70 dark:text-ivory/60">
                    Total: {importPreview.total_rows}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold">
                    Valid: {importPreview.valid_rows_count}
                  </span>
                  {importPreview.invalid_rows_count > 0 && (
                    <span className="px-2.5 py-0.5 rounded-full bg-rose/15 text-rose text-xs font-mono font-bold">
                      Invalid: {importPreview.invalid_rows_count}
                    </span>
                  )}
                </div>
              </div>

              {/* Rows Table */}
              <div className="overflow-x-auto rounded-2xl border border-slate/10 dark:border-white/5">
                <table className="w-full text-left text-xs font-sans">
                  <thead className="bg-slate/10 dark:bg-white/5 font-mono text-[11px] uppercase text-slate/60 dark:text-ivory/50">
                    <tr>
                      <th className="py-2.5 px-3">Row</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Tech & Topic</th>
                      <th className="py-2.5 px-3">Difficulty</th>
                      <th className="py-2.5 px-3">Question Text</th>
                      <th className="py-2.5 px-3">Validation Issues</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate/10 dark:divide-white/5">
                    {importPreview.rows.map((r) => (
                      <tr key={r.row_index} className={r.is_valid ? 'bg-transparent' : 'bg-rose/5'}>
                        <td className="py-3 px-3 font-mono text-slate/50">#{r.row_index}</td>
                        <td className="py-3 px-3">
                          {r.is_valid ? (
                            <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-600 dark:text-emerald-400 uppercase">
                              <CheckCircle2 size={13} /> Valid
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold text-rose uppercase">
                              <XCircle size={13} /> Error
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-mono text-[11px]">
                          {r.technology} &gt; {r.topic}
                        </td>
                        <td className="py-3 px-3 font-mono text-[11px]">{r.difficulty}</td>
                        <td className="py-3 px-3 max-w-xs truncate font-medium text-charcoal dark:text-ivory">
                          {r.question_text}
                        </td>
                        <td className="py-3 px-3 text-[11px]">
                          {r.errors && r.errors.length > 0 ? (
                            <ul className="list-disc list-inside text-rose space-y-0.5">
                              {r.errors.map((err, i) => (
                                <li key={i}>{err}</li>
                              ))}
                            </ul>
                          ) : (
                            <span className="text-slate/40">None</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: ADD / EDIT GLOBAL QUESTION */}
      {/* ==================================================================== */}
      <GlassModal
        isOpen={showQuestionModal}
        onClose={() => setShowQuestionModal(false)}
        title={editingQuestion ? 'Edit Question' : 'Create Global Bank Question'}
      >
        <form onSubmit={handleSaveQuestion} className="space-y-5 text-charcoal dark:text-ivory">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
                Technology *
              </label>
              <input
                type="text"
                value={modalFormData.technology}
                onChange={(e) => setModalFormData({ ...modalFormData, technology: e.target.value })}
                placeholder="e.g. Python, React"
                required
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono min-h-[40px]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
                Topic *
              </label>
              <input
                type="text"
                value={modalFormData.topic}
                onChange={(e) => setModalFormData({ ...modalFormData, topic: e.target.value })}
                placeholder="e.g. AsyncIO, Hooks"
                required
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono min-h-[40px]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono font-bold uppercase text-slate/70 dark:text-ivory/60 mb-1">
                Difficulty *
              </label>
              <select
                value={modalFormData.difficulty}
                onChange={(e) => setModalFormData({ ...modalFormData, difficulty: e.target.value })}
                className="w-full bg-white dark:bg-charcoal-700 text-charcoal dark:text-ivory border border-slate/30 dark:border-white/20 rounded-xl px-3 py-2 text-xs font-mono min-h-[40px] focus:outline-none focus:border-oxblood"
              >
                <option value="BEGINNER" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Beginner</option>
                <option value="INTERMEDIATE" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Intermediate</option>
                <option value="ADVANCED" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Advanced</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
              Question Text *
            </label>
            <textarea
              rows={3}
              value={modalFormData.question_text}
              onBlur={handleCheckDuplicate}
              onChange={(e) => setModalFormData({ ...modalFormData, question_text: e.target.value })}
              placeholder="Enter comprehensive, unambiguous question text..."
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl p-3 text-xs font-sans text-charcoal dark:text-ivory"
            />
            {duplicateWarning && (
              <p className="mt-1 text-xs text-amber-500 font-mono flex items-center gap-1">
                <AlertCircle size={13} /> {duplicateWarning}
              </p>
            )}
          </div>

          {/* Options */}
          <div className="space-y-2">
            <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50">
              Answer Options (Select correct radio button) *
            </label>
            {modalFormData.options.map((opt, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="correct_option"
                  checked={opt.is_correct}
                  onChange={() => {
                    const updated = modalFormData.options.map((o, i) => ({
                      ...o,
                      is_correct: i === idx
                    }));
                    setModalFormData({ ...modalFormData, options: updated });
                  }}
                  className="w-4 h-4 accent-oxblood"
                  title="Mark as correct answer"
                />
                <span className="w-6 font-mono text-xs font-bold text-slate/50">
                  {opt.option_key}
                </span>
                <input
                  type="text"
                  value={opt.option_text}
                  onChange={(e) => {
                    const updated = [...modalFormData.options];
                    updated[idx] = { ...updated[idx], option_text: e.target.value };
                    setModalFormData({ ...modalFormData, options: updated });
                  }}
                  placeholder={`Option ${opt.option_key} text...`}
                  required
                  className="flex-1 bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-sans min-h-[38px]"
                />
              </div>
            ))}
          </div>

          {/* Explanation */}
          <div>
            <label className="block text-[11px] font-mono font-bold uppercase text-slate/60 dark:text-ivory/50 mb-1">
              Detailed Explanation / Solution Reference
            </label>
            <textarea
              rows={2}
              value={modalFormData.explanation}
              onChange={(e) => setModalFormData({ ...modalFormData, explanation: e.target.value })}
              placeholder="Why this answer is correct..."
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl p-3 text-xs font-sans text-charcoal dark:text-ivory"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate/10 dark:border-white/5">
            <button
              type="button"
              onClick={() => setShowQuestionModal(false)}
              className="px-4 py-2 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono font-bold uppercase min-h-[40px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={savingQuestion}
              className="px-5 py-2 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase min-h-[40px]"
            >
              {savingQuestion ? 'Saving...' : editingQuestion ? 'Update Question' : 'Create Question'}
            </button>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};

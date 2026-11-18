import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Search, Filter, Plus, Copy, Check, X, AlertCircle,
  FolderPlus, Layers, BookOpen, Tag, Award, HelpCircle, Eye,
  Sparkles, CheckCircle2, ChevronRight, RefreshCw, FileText, Edit3, Archive
} from 'lucide-react';
import { questionBankAPI } from '../services/api';
import { GlassModal, useToast, AnimatedCounter } from './MotionComponents';

export const RecruiterQuestionBankTab = () => {
  const { addToast } = useToast();

  const [activeSubTab, setActiveSubTab] = useState('browse'); // 'browse' | 'collections'
  const [questions, setQuestions] = useState([]);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedTech, setSelectedTech] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('');
  const [scopeFilter, setScopeFilter] = useState('ALL'); // 'ALL' | 'GLOBAL' | 'CUSTOM'

  // Technologies metadata from backend
  const [techMetadata, setTechMetadata] = useState({ technologies: [], topics_by_technology: {} });

  // Collections state
  const [collections, setCollections] = useState([]);
  const [loadingCollections, setLoadingCollections] = useState(false);
  const [showCreateCollectionModal, setShowCreateCollectionModal] = useState(false);
  const [collectionFormData, setCollectionFormData] = useState({
    name: '',
    description: '',
    technology: 'Python',
    question_ids: []
  });

  // Modal: Create Custom Question
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [questionFormData, setQuestionFormData] = useState({
    technology: 'Python',
    topic: 'Core',
    subtopic: '',
    difficulty: 'INTERMEDIATE',
    marks: 5,
    explanation: '',
    tags: '',
    question_text: '',
    options: [
      { option_key: 'A', option_text: '', is_correct: true },
      { option_key: 'B', option_text: '', is_correct: false },
      { option_key: 'C', option_text: '', is_correct: false },
      { option_key: 'D', option_text: '', is_correct: false },
    ]
  });

  // Duplicate Check Feedback
  const [duplicateCheckResult, setDuplicateCheckResult] = useState(null);
  const [isCheckingDuplicate, setIsCheckingDuplicate] = useState(false);

  // Modal: Inspect Question Details
  const [inspectQuestion, setInspectQuestion] = useState(null);

  // Modal: View Collection Details
  const [inspectCollection, setInspectCollection] = useState(null);
  const [collectionDetailsLoading, setCollectionDetailsLoading] = useState(false);

  // Fetch technologies & topics catalog
  const fetchTechnologies = async () => {
    try {
      const res = await questionBankAPI.getTechnologies();
      const data = res.data || {};
      const techs = Array.isArray(data.technologies)
        ? data.technologies.map((t) => (typeof t === 'string' ? t : t.technology || String(t)))
        : [];
      setTechMetadata({
        technologies: techs,
        topics_by_technology: data.topics_by_technology || {}
      });
    } catch (err) {
      console.error('Failed to load technologies metadata:', err);
    }
  };

  // Fetch Questions
  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const params = {
        page: 1,
        limit: 100,
        include_custom: true
      };
      if (search.trim()) params.search = search.trim();
      if (selectedTech) params.technology = selectedTech;
      if (selectedTopic) params.topic = selectedTopic;
      if (selectedDifficulty) params.difficulty = selectedDifficulty;

      const res = await questionBankAPI.list(params);
      let items = res.data?.items || [];

      if (scopeFilter === 'GLOBAL') {
        items = items.filter((q) => q.is_global);
      } else if (scopeFilter === 'CUSTOM') {
        items = items.filter((q) => !q.is_global);
      }

      setQuestions(items);
      setTotalQuestions(res.data?.total ?? items.length);
    } catch (err) {
      console.error('Failed to load question bank:', err);
      addToast('Failed to load question bank.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch Collections
  const fetchCollections = async () => {
    try {
      setLoadingCollections(true);
      const res = await questionBankAPI.listCollections();
      setCollections(res.data || []);
    } catch (err) {
      console.error('Failed to load collections:', err);
    } finally {
      setLoadingCollections(false);
    }
  };

  useEffect(() => {
    fetchTechnologies();
    fetchCollections();
  }, []);

  useEffect(() => {
    const delay = setTimeout(() => {
      fetchQuestions();
    }, 250);
    return () => clearTimeout(delay);
  }, [search, selectedTech, selectedTopic, selectedDifficulty, scopeFilter]);

  // Live duplicate detection debounced
  useEffect(() => {
    if (!showCreateModal) {
      setDuplicateCheckResult(null);
      return;
    }

    const text = questionFormData.question_text.trim();
    if (text.length < 15) {
      setDuplicateCheckResult(null);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsCheckingDuplicate(true);
        const res = await questionBankAPI.checkDuplicate({
          question_text: text,
          exclude_id: editingQuestion ? editingQuestion.id : null
        });
        setDuplicateCheckResult(res.data);
      } catch (err) {
        console.error('Duplicate check error:', err);
      } finally {
        setIsCheckingDuplicate(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [questionFormData.question_text, showCreateModal, editingQuestion]);

  // Open Create Custom Question Modal
  const handleOpenCreateModal = () => {
    setEditingQuestion(null);
    setDuplicateCheckResult(null);
    setQuestionFormData({
      technology: selectedTech || (techMetadata.technologies[0] || 'Python'),
      topic: selectedTopic || 'Core Language',
      subtopic: '',
      difficulty: 'INTERMEDIATE',
      marks: 5,
      explanation: '',
      tags: '',
      question_text: '',
      options: [
        { option_key: 'A', option_text: '', is_correct: true },
        { option_key: 'B', option_text: '', is_correct: false },
        { option_key: 'C', option_text: '', is_correct: false },
        { option_key: 'D', option_text: '', is_correct: false },
      ]
    });
    setShowCreateModal(true);
  };

  // Open Edit Custom Question Modal
  const handleOpenEditModal = (q) => {
    setEditingQuestion(q);
    setDuplicateCheckResult(null);
    setQuestionFormData({
      technology: q.technology,
      topic: q.topic,
      subtopic: q.subtopic || '',
      difficulty: q.difficulty,
      marks: q.marks,
      explanation: q.explanation || '',
      tags: (q.tags || []).join(', '),
      question_text: q.question_text,
      options: (q.options || []).map((o) => ({
        option_key: o.option_key,
        option_text: o.option_text,
        is_correct: o.is_correct || false
      }))
    });
    setShowCreateModal(true);
  };

  // Duplicate Global Question into Custom Question
  const handleDuplicateToCustom = async (question) => {
    try {
      const res = await questionBankAPI.duplicate(question.id);
      addToast(`Question duplicated to your custom bank as "${res.data.question_text.slice(0, 30)}..."`, 'success');
      fetchQuestions();
    } catch (err) {
      console.error('Failed to duplicate question:', err);
      addToast(err.response?.data?.detail || 'Failed to duplicate question.', 'error');
    }
  };

  // Archive Custom Question
  const handleArchiveQuestion = async (q) => {
    if (!window.confirm(`Archive custom question: "${q.question_text.slice(0, 40)}..."?`)) return;
    try {
      await questionBankAPI.archive(q.id);
      addToast('Question archived successfully', 'success');
      fetchQuestions();
    } catch (err) {
      console.error('Failed to archive question:', err);
      addToast(err.response?.data?.detail || 'Failed to archive question.', 'error');
    }
  };

  // Save Custom Question Form
  const handleSaveQuestion = async (e) => {
    e.preventDefault();

    if (!questionFormData.question_text.trim()) {
      addToast('Please enter the question prompt.', 'error');
      return;
    }

    for (let i = 0; i < questionFormData.options.length; i++) {
      if (!questionFormData.options[i].option_text.trim()) {
        addToast(`Option ${questionFormData.options[i].option_key} cannot be blank.`, 'error');
        return;
      }
    }

    const hasCorrect = questionFormData.options.some((o) => o.is_correct);
    if (!hasCorrect) {
      addToast('Please mark one correct option.', 'error');
      return;
    }

    const payload = {
      technology: questionFormData.technology,
      topic: questionFormData.topic,
      subtopic: questionFormData.subtopic || null,
      difficulty: questionFormData.difficulty,
      marks: Number(questionFormData.marks) || 5,
      explanation: questionFormData.explanation || null,
      tags: questionFormData.tags ? questionFormData.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      question_text: questionFormData.question_text.trim(),
      options: questionFormData.options.map((o) => ({
        option_key: o.option_key,
        option_text: o.option_text.trim(),
        is_correct: o.is_correct
      }))
    };

    try {
      if (editingQuestion) {
        await questionBankAPI.update(editingQuestion.id, payload);
        addToast('Custom question updated successfully!', 'success');
      } else {
        await questionBankAPI.create(payload);
        addToast('Custom question created in your repository!', 'success');
      }
      setShowCreateModal(false);
      fetchQuestions();
    } catch (err) {
      console.error('Failed to save question:', err);
      addToast(err.response?.data?.detail || 'Failed to save question.', 'error');
    }
  };

  // Inspect Collection Details
  const handleInspectCollection = async (collection) => {
    try {
      setCollectionDetailsLoading(true);
      setShowCreateCollectionModal(false);
      const res = await questionBankAPI.getCollection(collection.id);
      setInspectCollection(res.data);
    } catch (err) {
      console.error('Failed to load collection details:', err);
      addToast('Failed to load collection questions.', 'error');
    } finally {
      setCollectionDetailsLoading(false);
    }
  };

  // Create Collection Form
  const handleSaveCollection = async (e) => {
    e.preventDefault();
    if (!collectionFormData.name.trim()) {
      addToast('Please enter a collection name.', 'error');
      return;
    }
    if (collectionFormData.question_ids.length === 0) {
      addToast('Select at least one question for this collection.', 'error');
      return;
    }

    try {
      await questionBankAPI.createCollection(collectionFormData);
      addToast(`Collection "${collectionFormData.name}" created!`, 'success');
      setShowCreateCollectionModal(false);
      setCollectionFormData({ name: '', description: '', technology: 'Python', question_ids: [] });
      fetchCollections();
    } catch (err) {
      console.error('Failed to create collection:', err);
      addToast(err.response?.data?.detail || 'Failed to create collection.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Sub-Navigation Pills */}
      <div className="flex border-b border-slate/15 dark:border-rose/15 space-x-2 overflow-x-auto pb-1">
        <button
          onClick={() => setActiveSubTab('browse')}
          className={`flex items-center gap-2 py-2.5 px-4 text-xs font-mono font-bold uppercase tracking-wider rounded-xl transition-all min-h-[40px] ${
            activeSubTab === 'browse'
              ? 'bg-oxblood text-ivory shadow-sm'
              : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory bg-slate/5 dark:bg-white/5'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Technical Question Repository</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/20 text-ivory">
            {totalQuestions}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('collections')}
          className={`flex items-center gap-2 py-2.5 px-4 text-xs font-mono font-bold uppercase tracking-wider rounded-xl transition-all min-h-[40px] ${
            activeSubTab === 'collections'
              ? 'bg-oxblood text-ivory shadow-sm'
              : 'text-slate/70 dark:text-ivory/60 hover:text-charcoal dark:hover:text-ivory bg-slate/5 dark:bg-white/5'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Curated Collections</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/20 text-ivory">
            {collections.length}
          </span>
        </button>
      </div>

      {activeSubTab === 'browse' && (
        <div className="space-y-6">
          {/* Filter & Action Toolbar */}
          <div className="glass-card p-5 sm:p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl space-y-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Search Bar */}
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate/40 dark:text-ivory/40" />
                <input
                  type="text"
                  placeholder="Search questions by keyword, topic, or tags..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 text-xs font-sans text-charcoal dark:text-ivory min-h-[44px]"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2.5">
                <button
                  onClick={handleOpenCreateModal}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-oxblood hover:bg-oxblood/80 text-ivory text-xs font-mono font-bold uppercase tracking-wider shadow-sm min-h-[44px]"
                >
                  <Plus size={15} /> Create Custom Question
                </button>
              </div>
            </div>

            {/* Filter Pills Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 font-mono text-xs">
              {/* Technology Filter */}
              <div>
                <label className="block text-[10px] uppercase text-slate/50 dark:text-ivory/40 mb-1">Technology</label>
                <select
                  value={selectedTech}
                  onChange={(e) => {
                    setSelectedTech(e.target.value);
                    setSelectedTopic('');
                  }}
                  className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono min-h-[38px] text-charcoal dark:text-ivory"
                >
                  <option value="">All Technologies</option>
                  {(techMetadata.technologies || []).map((t) => {
                    const val = typeof t === 'string' ? t : t.technology || String(t);
                    return (
                      <option key={val} value={val} className="bg-charcoal text-ivory">{val}</option>
                    );
                  })}
                </select>
              </div>

              {/* Topic Filter */}
              <div>
                <label className="block text-[10px] uppercase text-slate/50 dark:text-ivory/40 mb-1">Topic</label>
                <select
                  value={selectedTopic}
                  disabled={!selectedTech}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                  className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono min-h-[38px] text-charcoal dark:text-ivory disabled:opacity-40"
                >
                  <option value="">All Topics</option>
                  {selectedTech && (techMetadata.topics_by_technology[selectedTech] || []).map((tp) => (
                    <option key={tp} value={tp} className="bg-charcoal text-ivory">{tp}</option>
                  ))}
                </select>
              </div>

              {/* Difficulty Filter */}
              <div>
                <label className="block text-[10px] uppercase text-slate/50 dark:text-ivory/40 mb-1">Difficulty</label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono min-h-[38px] text-charcoal dark:text-ivory"
                >
                  <option value="">All Difficulties</option>
                  <option value="BEGINNER" className="bg-charcoal text-ivory">Beginner</option>
                  <option value="INTERMEDIATE" className="bg-charcoal text-ivory">Intermediate</option>
                  <option value="ADVANCED" className="bg-charcoal text-ivory">Advanced</option>
                </select>
              </div>

              {/* Scope Filter */}
              <div>
                <label className="block text-[10px] uppercase text-slate/50 dark:text-ivory/40 mb-1">Repository Scope</label>
                <select
                  value={scopeFilter}
                  onChange={(e) => setScopeFilter(e.target.value)}
                  className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-mono min-h-[38px] text-charcoal dark:text-ivory"
                >
                  <option value="ALL" className="bg-charcoal text-ivory">All Items (Global + Custom)</option>
                  <option value="GLOBAL" className="bg-charcoal text-ivory">Standard Global Bank Only</option>
                  <option value="CUSTOM" className="bg-charcoal text-ivory">My Custom Questions Only</option>
                </select>
              </div>
            </div>
          </div>

          {/* Questions Grid */}
          {loading ? (
            <div className="py-20 text-center font-mono text-xs text-slate/50 flex items-center justify-center gap-2">
              <RefreshCw className="w-5 h-5 animate-spin text-oxblood" />
              <span>Querying technical question repository...</span>
            </div>
          ) : questions.length === 0 ? (
            <div className="p-12 text-center rounded-3xl bg-slate/5 dark:bg-white/5 border border-dashed border-slate/20 dark:border-rose/20 space-y-3 font-mono">
              <Database className="w-10 h-10 text-slate/40 dark:text-rose/40 mx-auto" />
              <h3 className="font-display font-bold text-sm text-charcoal dark:text-ivory">No Questions Match Criteria</h3>
              <p className="text-xs text-slate/50 dark:text-ivory/50 max-w-sm mx-auto font-sans">
                Try widening your technology or topic filters, or create a new custom technical question.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {questions.map((q) => (
                <div
                  key={q.id}
                  className="glass-card p-5 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-md flex flex-col justify-between space-y-4 hover:border-oxblood/40 transition-colors"
                >
                  <div>
                    {/* Header Chips */}
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="px-2 py-0.5 rounded-full bg-oxblood/10 text-oxblood dark:text-rose border border-oxblood/20 text-[10px] font-mono font-bold">
                          {q.technology}
                        </span>
                        <span className="text-[10px] font-mono text-slate/50 dark:text-ivory/40">
                          {q.topic}
                        </span>
                      </div>

                      <div className="flex items-center gap-1">
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                          q.difficulty === 'BEGINNER' ? 'badge-selected' : q.difficulty === 'ADVANCED' ? 'badge-oxblood' : 'badge-slate'
                        }`}>
                          {q.difficulty}
                        </span>
                      </div>
                    </div>

                    {/* Question Prompt */}
                    <h4 className="font-sans font-semibold text-sm text-charcoal dark:text-ivory leading-snug line-clamp-3">
                      {q.question_text}
                    </h4>

                    {/* Meta info */}
                    <div className="mt-3 pt-3 border-t border-slate/10 dark:border-white/5 flex items-center justify-between text-[11px] font-mono text-slate/50 dark:text-ivory/40">
                      <span>{q.options?.length || 4} Options &bull; {q.marks} Mark(s)</span>
                      <span className={q.is_global ? 'text-slate/60' : 'text-oxblood dark:text-rose font-bold'}>
                        {q.is_global ? 'Global Bank' : 'Custom Question'}
                      </span>
                    </div>

                    {/* Tags */}
                    {q.tags && q.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {q.tags.slice(0, 3).map((tag, idx) => (
                          <span key={idx} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate/10 dark:bg-white/5 text-slate/60 dark:text-ivory/50">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-2 border-t border-slate/10 dark:border-white/5 flex items-center gap-2 font-mono text-xs flex-wrap">
                    <button
                      type="button"
                      onClick={() => setInspectQuestion(q)}
                      className="flex-1 py-2 px-3 rounded-xl bg-slate/5 dark:bg-white/5 hover:bg-slate/10 dark:hover:bg-white/10 text-charcoal dark:text-ivory flex items-center justify-center gap-1.5 min-h-[38px] font-semibold"
                    >
                      <Eye size={13} /> View
                    </button>

                    {!q.is_global ? (
                      <>
                        <button
                          type="button"
                          onClick={() => handleOpenEditModal(q)}
                          className="py-2 px-3 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-slate/15 text-charcoal dark:text-ivory flex items-center justify-center gap-1 min-h-[38px] font-semibold"
                          title="Edit custom question"
                        >
                          <Edit3 size={13} /> Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleArchiveQuestion(q)}
                          className="py-2 px-2.5 rounded-xl bg-rose/10 hover:bg-rose/20 text-rose flex items-center justify-center min-h-[38px]"
                          title="Archive question"
                        >
                          <Archive size={13} />
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleDuplicateToCustom(q)}
                        title="Duplicate this question to customize marks or text"
                        className="py-2 px-3 rounded-xl bg-slate/10 dark:bg-white/10 hover:bg-oxblood/15 hover:text-oxblood dark:hover:text-rose flex items-center justify-center gap-1.5 min-h-[38px] text-slate/70 dark:text-ivory/70 transition-colors"
                      >
                        <Copy size={13} /> Duplicate
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SUBTAB 2: COLLECTIONS */}
      {activeSubTab === 'collections' && (
        <div className="space-y-6">
          <div className="glass-card p-6 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h3 className="font-display text-lg font-bold text-charcoal dark:text-ivory flex items-center gap-2">
                <Layers className="w-5 h-5 text-oxblood dark:text-rose" />
                Technical Assessment Collections
              </h3>
              <p className="text-xs font-mono text-slate/60 dark:text-ivory/50 mt-1">
                Group frequently evaluated questions into reusable templates for quick assessment authoring.
              </p>
            </div>
            <button
              onClick={() => {
                const defaultTech = selectedTech || (techMetadata.technologies[0] || 'Python');
                setCollectionFormData({
                  name: '',
                  description: '',
                  technology: typeof defaultTech === 'string' ? defaultTech : 'Python',
                  question_ids: []
                });
                setShowCreateCollectionModal(true);
              }}
              className="px-4 py-2.5 rounded-xl bg-oxblood text-ivory text-xs font-mono font-bold uppercase tracking-wider flex items-center gap-2 shadow-sm min-h-[44px]"
            >
              <FolderPlus size={15} /> New Collection
            </button>
          </div>

          {loadingCollections ? (
            <div className="py-16 text-center font-mono text-xs text-slate/50">
              Loading collections...
            </div>
          ) : collections.length === 0 ? (
            <div className="p-12 text-center rounded-3xl bg-slate/5 dark:bg-white/5 border border-dashed border-slate/20 dark:border-rose/20 space-y-2 font-mono">
              <Layers className="w-10 h-10 text-slate/40 dark:text-rose/40 mx-auto" />
              <p className="text-xs text-slate/50 dark:text-ivory/50 font-sans">
                No question collections created yet. Bundle questions into custom sets for rapid reuse.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {collections.map((col) => (
                <div
                  key={col.id}
                  className="glass-card p-5 rounded-3xl border border-slate/15 dark:border-rose/15 shadow-md flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="px-2 py-0.5 rounded-full bg-oxblood/10 text-oxblood dark:text-rose border border-oxblood/20 text-[10px] font-mono font-bold">
                        {col.technology || 'General'}
                      </span>
                      <span className="text-[10px] font-mono text-slate/50">
                        {col.question_count} Questions
                      </span>
                    </div>
                    <h4 className="font-display font-bold text-base text-charcoal dark:text-ivory">
                      {col.name}
                    </h4>
                    {col.description && (
                      <p className="text-xs text-slate/60 dark:text-ivory/60 line-clamp-2">
                        {col.description}
                      </p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate/10 dark:border-white/5 flex justify-end">
                    <button
                      onClick={() => handleInspectCollection(col)}
                      className="px-4 py-2 rounded-xl bg-slate/5 dark:bg-white/5 hover:bg-slate/10 dark:hover:bg-white/10 text-xs font-mono font-semibold flex items-center gap-1.5 min-h-[38px]"
                    >
                      <Eye size={13} /> View Questions
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 1: CREATE / EDIT CUSTOM QUESTION */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={editingQuestion ? 'Edit Custom Technical Question' : 'Create Custom Technical Question'}
        subtitle="Saved to your recruiter-specific technical question bank"
      >
        <form onSubmit={handleSaveQuestion} className="space-y-5 text-charcoal dark:text-ivory max-h-[75vh] overflow-y-auto pr-1">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                Technology *
              </label>
              <select
                value={questionFormData.technology}
                onChange={(e) => setQuestionFormData({ ...questionFormData, technology: e.target.value })}
                required
                className="w-full bg-white dark:bg-charcoal-700 text-charcoal dark:text-ivory border border-slate/30 dark:border-white/20 rounded-xl px-3 py-2 min-h-[40px] text-xs font-mono focus:outline-none focus:border-oxblood"
              >
                {(techMetadata.technologies.length > 0 ? techMetadata.technologies : ['Python', 'JavaScript', 'React', 'SQL', 'DSA', 'Java']).map((t) => {
                  const val = typeof t === 'string' ? t : t.technology || String(t);
                  return (
                    <option key={val} value={val} className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">{val}</option>
                  );
                })}
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                Topic *
              </label>
              <input
                type="text"
                value={questionFormData.topic}
                onChange={(e) => setQuestionFormData({ ...questionFormData, topic: e.target.value })}
                placeholder="e.g. AsyncIO, Indexes, Hooks"
                required
                className="w-full bg-white dark:bg-charcoal-700 text-charcoal dark:text-ivory border border-slate/30 dark:border-white/20 rounded-xl px-3 py-2 min-h-[40px] text-xs font-mono focus:outline-none focus:border-oxblood"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                Difficulty *
              </label>
              <select
                value={questionFormData.difficulty}
                onChange={(e) => setQuestionFormData({ ...questionFormData, difficulty: e.target.value })}
                className="w-full bg-white dark:bg-charcoal-700 text-charcoal dark:text-ivory border border-slate/30 dark:border-white/20 rounded-xl px-3 py-2 min-h-[40px] text-xs font-mono focus:outline-none focus:border-oxblood"
              >
                <option value="BEGINNER" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Beginner</option>
                <option value="INTERMEDIATE" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Intermediate</option>
                <option value="ADVANCED" className="bg-white dark:bg-charcoal-800 text-charcoal dark:text-ivory">Advanced</option>
              </select>
            </div>
          </div>

          {/* Question Text */}
          <div>
            <label className="block text-[10px] uppercase font-mono font-bold text-slate/50 dark:text-ivory/40 mb-1">
              Question Prompt *
            </label>
            <textarea
              rows={3}
              value={questionFormData.question_text}
              onChange={(e) => setQuestionFormData({ ...questionFormData, question_text: e.target.value })}
              placeholder="Enter clear, precise technical question prompt..."
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl p-3 text-xs font-sans min-h-[60px]"
            />
          </div>

          {/* Live Duplicate Warning Box */}
          {isCheckingDuplicate && (
            <div className="p-2.5 rounded-xl bg-slate/5 text-[11px] font-mono text-slate/50 flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-oxblood" /> Checking for similar questions in bank...
            </div>
          )}

          {duplicateCheckResult && duplicateCheckResult.is_duplicate && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 font-mono text-xs space-y-1"
            >
              <div className="flex items-center gap-2 font-bold">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>Potential Duplicate Warning</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                {duplicateCheckResult.similarity_reason || 'A very similar question already exists in this subject in the central repository.'}
              </p>
              <span className="text-[10px] text-slate/50 dark:text-ivory/40 block">
                You may still save this question if you are testing a distinct variation.
              </span>
            </motion.div>
          )}

          {/* Options */}
          <div className="space-y-2.5">
            <label className="block text-[10px] uppercase font-mono font-bold text-slate/50 dark:text-ivory/40">
              Multiple Choice Options (Select radio for the correct answer):
            </label>
            {questionFormData.options.map((opt, optIdx) => (
              <div key={optIdx} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="custom_qb_correct_opt"
                  checked={opt.is_correct}
                  onChange={() => {
                    const opts = questionFormData.options.map((o, i) => ({
                      ...o,
                      is_correct: i === optIdx
                    }));
                    setQuestionFormData({ ...questionFormData, options: opts });
                  }}
                  className="w-4 h-4 text-oxblood cursor-pointer"
                  title="Mark as correct answer"
                />
                <span className="w-5 text-xs font-mono font-bold text-oxblood dark:text-rose">
                  {opt.option_key}.
                </span>
                <input
                  type="text"
                  placeholder={`Option ${opt.option_key} text...`}
                  value={opt.option_text}
                  onChange={(e) => {
                    const val = e.target.value;
                    const opts = [...questionFormData.options];
                    opts[optIdx] = { ...opts[optIdx], option_text: val };
                    setQuestionFormData({ ...questionFormData, options: opts });
                  }}
                  required
                  className="flex-1 bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 text-xs font-sans min-h-[38px]"
                />
              </div>
            ))}
          </div>

          {/* Explanation & Marks */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            <div className="sm:col-span-2">
              <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                Explanation (Shown after candidate submits)
              </label>
              <input
                type="text"
                value={questionFormData.explanation}
                onChange={(e) => setQuestionFormData({ ...questionFormData, explanation: e.target.value })}
                placeholder="Why the correct option is right..."
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 min-h-[40px] text-xs font-sans"
              />
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate/50 dark:text-ivory/40 mb-1">
                Marks
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={questionFormData.marks}
                onChange={(e) => setQuestionFormData({ ...questionFormData, marks: parseInt(e.target.value, 10) || 1 })}
                className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 min-h-[40px] text-xs font-mono"
              />
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-[10px] uppercase font-mono font-bold text-slate/50 dark:text-ivory/40 mb-1">
              Comma-Separated Tags
            </label>
            <input
              type="text"
              value={questionFormData.tags}
              onChange={(e) => setQuestionFormData({ ...questionFormData, tags: e.target.value })}
              placeholder="e.g. core-python, data-structures, arrays"
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 dark:border-white/10 rounded-xl px-3 py-2 min-h-[40px] text-xs font-mono"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-3 border-t border-slate/15 dark:border-white/10 font-mono">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 text-xs uppercase min-h-[44px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase min-h-[44px] shadow-sm"
            >
              {editingQuestion ? 'Update Question' : 'Save Custom Question'}
            </button>
          </div>
        </form>
      </GlassModal>

      {/* ======================================================== */}
      {/* MODAL 2: INSPECT QUESTION DETAILS */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(inspectQuestion)}
        onClose={() => setInspectQuestion(null)}
        title="Question Bank Inspector"
        subtitle={`${inspectQuestion?.technology} • ${inspectQuestion?.topic}`}
      >
        {inspectQuestion && (
          <div className="space-y-5 text-charcoal dark:text-ivory text-xs font-mono">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="badge-oxblood px-2.5 py-0.5 rounded-full font-bold">
                {inspectQuestion.technology}
              </span>
              <span className="badge-slate px-2.5 py-0.5 rounded-full font-bold">
                {inspectQuestion.difficulty}
              </span>
              <span className="badge-selected px-2.5 py-0.5 rounded-full font-bold">
                {inspectQuestion.marks} Mark(s)
              </span>
              <span className="text-[10px] text-slate/50">
                Usage: {inspectQuestion.usage_count || 0} times
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate/5 dark:bg-white/5 border border-slate/15 dark:border-white/10 space-y-2 font-sans">
              <p className="text-sm font-semibold text-charcoal dark:text-ivory leading-relaxed">
                {inspectQuestion.question_text}
              </p>
            </div>

            {/* Options */}
            <div className="space-y-2">
              <p className="text-[10px] uppercase font-bold text-slate/50">Options:</p>
              {inspectQuestion.options?.map((opt) => (
                <div
                  key={opt.id || opt.option_key}
                  className={`p-3 rounded-xl border flex items-center justify-between text-xs font-sans ${
                    opt.is_correct
                      ? 'bg-success/15 border-success/30 text-success font-semibold'
                      : 'bg-white/5 border-slate/10 dark:border-white/5 text-slate/70 dark:text-ivory/70'
                  }`}
                >
                  <span><strong>{opt.option_key}.</strong> {opt.option_text}</span>
                  {opt.is_correct && (
                    <span className="text-[10px] font-mono uppercase bg-success/20 px-2 py-0.5 rounded font-bold">
                      Correct
                    </span>
                  )}
                </div>
              ))}
            </div>

            {inspectQuestion.explanation && (
              <div className="p-3.5 rounded-xl bg-oxblood/10 border border-oxblood/20 text-oxblood dark:text-rose space-y-1 font-sans">
                <span className="font-mono text-[10px] font-bold uppercase">Explanation:</span>
                <p className="text-xs leading-relaxed">{inspectQuestion.explanation}</p>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setInspectQuestion(null)}
                className="px-5 py-2.5 rounded-xl bg-slate/10 dark:bg-white/10 text-xs font-mono uppercase min-h-[40px]"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </GlassModal>

      {/* ======================================================== */}
      {/* MODAL 3: CREATE COLLECTION */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={showCreateCollectionModal}
        onClose={() => setShowCreateCollectionModal(false)}
        title="Create Technical Question Collection"
        subtitle="Curate reusable bundles for rapid assessment generation"
      >
        <form onSubmit={handleSaveCollection} className="space-y-5 text-charcoal dark:text-ivory text-xs font-mono max-h-[75vh] overflow-y-auto pr-1">
          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
              Collection Name *
            </label>
            <input
              type="text"
              value={collectionFormData.name}
              onChange={(e) => setCollectionFormData({ ...collectionFormData, name: e.target.value })}
              placeholder="e.g. Senior Backend Python & DSA Essentials"
              required
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs font-sans min-h-[40px]"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
              Description
            </label>
            <input
              type="text"
              value={collectionFormData.description}
              onChange={(e) => setCollectionFormData({ ...collectionFormData, description: e.target.value })}
              placeholder="Brief summary of target competencies..."
              className="w-full bg-slate/5 dark:bg-white/5 border border-slate/20 rounded-xl px-3 py-2 text-xs font-sans min-h-[40px]"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-bold text-slate/50 mb-1">
              Select Questions to Include ({collectionFormData.question_ids.length} Selected)
            </label>
            <div className="space-y-2 max-h-56 overflow-y-auto border border-slate/15 rounded-xl p-2 bg-black/10">
              {questions.map((q) => {
                const isSelected = collectionFormData.question_ids.includes(q.id);
                return (
                  <div
                    key={q.id}
                    onClick={() => {
                      setCollectionFormData((prev) => ({
                        ...prev,
                        question_ids: isSelected
                          ? prev.question_ids.filter((id) => id !== q.id)
                          : [...prev.question_ids, q.id]
                      }));
                    }}
                    className={`p-2.5 rounded-lg border flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-oxblood/15 border-oxblood text-ivory'
                        : 'bg-white/5 border-slate/10 hover:bg-white/10 text-slate/70 dark:text-ivory/70'
                    }`}
                  >
                    <div className="flex items-center gap-2 max-w-[85%]">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="w-3.5 h-3.5 text-oxblood cursor-pointer"
                      />
                      <span className="font-sans text-xs truncate">{q.question_text}</span>
                    </div>
                    <span className="text-[10px] font-mono uppercase">{q.technology}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate/15 font-mono">
            <button
              type="button"
              onClick={() => setShowCreateCollectionModal(false)}
              className="px-4 py-2 rounded-xl bg-slate/10 text-xs uppercase min-h-[40px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-oxblood text-ivory text-xs font-bold uppercase min-h-[40px]"
            >
              Create Collection
            </button>
          </div>
        </form>
      </GlassModal>

      {/* ======================================================== */}
      {/* MODAL 4: VIEW COLLECTION QUESTIONS */}
      {/* ======================================================== */}
      <GlassModal
        isOpen={Boolean(inspectCollection)}
        onClose={() => setInspectCollection(null)}
        title={inspectCollection?.name || 'Collection'}
        subtitle={`${inspectCollection?.technology || 'Technical'} • ${inspectCollection?.questions?.length || 0} Questions`}
      >
        {inspectCollection && (
          <div className="space-y-4 text-charcoal dark:text-ivory text-xs font-mono max-h-[70vh] overflow-y-auto pr-1">
            {inspectCollection.description && (
              <p className="text-xs font-sans text-slate/70 dark:text-ivory/70 p-3 rounded-xl bg-slate/5 border border-slate/15">
                {inspectCollection.description}
              </p>
            )}

            <div className="space-y-3">
              {(inspectCollection.questions || []).map((q, idx) => (
                <div key={q.id} className="p-3.5 rounded-xl bg-slate/5 dark:bg-white/5 border border-slate/10 space-y-1.5">
                  <div className="flex justify-between items-center text-[11px]">
                    <span className="font-bold text-oxblood dark:text-rose">Q{idx + 1}. [{q.difficulty}]</span>
                    <span className="text-slate/50">{q.marks} Mark(s)</span>
                  </div>
                  <p className="font-sans text-xs font-medium text-charcoal dark:text-ivory">
                    {q.question_text}
                  </p>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setInspectCollection(null)}
                className="px-5 py-2.5 rounded-xl bg-slate/10 text-xs uppercase min-h-[40px]"
              >
                Close Collection
              </button>
            </div>
          </div>
        )}
      </GlassModal>
    </div>
  );
};

export default RecruiterQuestionBankTab;

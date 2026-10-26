// AI Study Buddy System — Realistic Mock Data & Store

export const initialNotebooks = [
  {
    id: 'nb-1',
    title: 'Machine Learning Fundamentals',
    course: 'CS229 / AI Graduate Track',
    sourcesCount: 5,
    lastActive: '12 minutes ago',
    progress: 74,
    color: '#3B82F6',
    pinned: true,
    description: 'Core supervised learning, gradient descent algorithms, backprop derivations, and empirical risk minimization.'
  },
  {
    id: 'nb-2',
    title: 'Data Structures and Algorithms',
    course: 'CS106B',
    sourcesCount: 6,
    lastActive: 'Yesterday',
    progress: 88,
    color: '#10B981',
    pinned: true,
    description: 'Graph traversals, dynamic programming paradigms, balanced BSTs, and amortized complexity bounds.'
  },
  {
    id: 'nb-3',
    title: 'Database Management Systems',
    course: 'CS145',
    sourcesCount: 4,
    lastActive: '3 days ago',
    progress: 62,
    color: '#8B5CF6',
    pinned: false,
    description: 'Relational algebra, B-Tree and LSM-tree indexing internals, ACID guarantees, and distributed 2PC.'
  },
  {
    id: 'nb-4',
    title: 'Computer Architecture and GPU Design',
    course: 'EE180',
    sourcesCount: 3,
    lastActive: 'Last week',
    progress: 41,
    color: '#F59E0B',
    pinned: false,
    description: 'Pipelining, branch prediction, SIMD execution vectors, warp scheduling, and GPU memory hierarchies.'
  }
];

export const initialSources = [
  {
    id: 'src-1',
    name: 'Deep_Learning_Goodfellow_Ch6.pdf',
    type: 'pdf',
    pages: 48,
    size: '4.8 MB',
    status: 'ready',
    active: true,
    addedDate: 'Oct 24, 2026',
    excerptPreview: 'Gradient descent is an iterative first-order optimization algorithm used to find a local minimum...'
  },
  {
    id: 'src-2',
    name: 'Stanford_CS229_Lecture4_Notes.pdf',
    type: 'pdf',
    pages: 18,
    size: '1.9 MB',
    status: 'ready',
    active: true,
    addedDate: 'Oct 24, 2026',
    excerptPreview: 'In Batch Gradient Descent, we calculate the gradient of the entire training dataset for each update...'
  },
  {
    id: 'src-3',
    name: 'Optimization_for_Deep_Learning.pptx',
    type: 'pptx',
    pages: 32,
    size: '8.4 MB',
    status: 'ready',
    active: true,
    addedDate: 'Oct 25, 2026',
    excerptPreview: 'Stochastic gradients introduce noise that helps escape shallow local saddles in high dimensional landscapes...'
  },
  {
    id: 'src-4',
    name: 'Backpropagation_Derivations.md',
    type: 'md',
    pages: '1.2k lines',
    size: '142 KB',
    status: 'ready',
    active: true,
    addedDate: 'Oct 25, 2026',
    excerptPreview: 'Applying the multivariate chain rule across composite computational graph nodes L -> a -> z -> w...'
  },
  {
    id: 'src-5',
    name: 'Gradient_Descent_Visualized_Lecture.mp4',
    type: 'video',
    pages: '42 min',
    size: '310 MB',
    status: 'ready',
    active: false,
    addedDate: 'Oct 26, 2026',
    excerptPreview: 'Video timestamp transcripts covering learning rate decay schedules, momentum vectors, and Adam optimizers...'
  }
];

export const citationsDatabase = {
  'cit-1': {
    id: 'cit-1',
    shortLabel: '[1]',
    sourceId: 'src-1',
    sourceName: 'Deep_Learning_Goodfellow_Ch6.pdf',
    pageNumber: 187,
    section: 'Section 6.5: First-Order Optimization Algorithms',
    quote: 'Gradient descent is an iterative first-order optimization algorithm used to find a local minimum of a differentiable function. To find a local minimum of a function using gradient descent, we take steps proportional to the negative of the gradient of the function at the current point: θ_{t+1} = θ_t - ε ∇_θ J(θ). If the step size ε is too small, convergence is slow; if too large, the algorithm can overshoot the valley and diverge.',
    relevanceConfidence: '98% grounded',
    relatedConcepts: ['Step Size (Learning Rate)', 'Convex Optimization', 'Gradient Norm Decay']
  },
  'cit-2': {
    id: 'cit-2',
    shortLabel: '[2]',
    sourceId: 'src-2',
    sourceName: 'Stanford_CS229_Lecture4_Notes.pdf',
    pageNumber: 8,
    section: 'Part 2: Batch vs Stochastic Gradient Descent',
    quote: 'In Batch Gradient Descent, we calculate the gradient of the entire training dataset for each update. While this guarantees smooth convergence on convex surfaces, calculating (1/N) ∑ ∇ L(x_i) becomes computationally prohibitive as N grows into millions, prompting Stochastic (SGD) and Mini-batch approximations.',
    relevanceConfidence: '95% grounded',
    relatedConcepts: ['Mini-batch SGD', 'Computational Complexity', 'Variance Reduction']
  }
};

export const initialMessages = [
  {
    id: 'msg-1',
    sender: 'user',
    timestamp: '10:14 AM',
    content: 'Explain gradient descent intuitively, then show the mathematical update rule.'
  },
  {
    id: 'msg-2',
    sender: 'tutor',
    timestamp: '10:14 AM',
    mode: 'Learn',
    content: `### 1. Intuitive Explanation: Fog on the Mountain

Imagine you are standing on a steep mountain shrouded in thick fog. You cannot see the lowest valley at the bottom of the mountain, but under your boots, you can feel the exact slope of the ground beneath your feet. 

To reach the bottom safely and efficiently, your natural strategy is:
1. **Feel the steepest direction** pointing downwards right where you stand.
2. **Take a controlled step** in that downward direction.
3. **Repeat** this process until the ground flattens out completely under your feet.

In Machine Learning, the mountain is your **Loss Function $L(w)$**, the elevation is your **prediction error**, and your coordinates on the map are your **model parameters $w$**.

---

### 2. The Mathematical Update Rule

Because the gradient $\\nabla L(w)$ mathematically points in the direction of *steepest ascent* (uphill), we move in the **opposite direction** (negative gradient) [cit-1]:

$$w_{t+1} = w_t - \\eta \\cdot \\nabla L(w_t)$$

Where:
- **$w_t$**: The current model parameter vector at iteration $t$.
- **$\\eta$ (Eta)**: The **learning rate** (step size). Controls how large of a step you take down the slope.
- **$\\nabla L(w_t)$**: The gradient vector—the partial derivatives $\\left[\\frac{\\partial L}{\\partial w_1}, \\frac{\\partial L}{\\partial w_2}, \\dots \\right]^T$ evaluated at the current parameters [cit-1].
- **$w_{t+1}$**: The updated, improved parameters for the next iteration.

---

### 3. Concrete 1D Numerical Example

Suppose our loss function is a simple convex parabola:
$$L(w) = w^2 \\quad \\implies \\quad \\nabla L(w) = \\frac{dL}{dw} = 2w$$

- Initial parameter: $w_0 = 4.0$
- Learning rate: $\\eta = 0.1$

**Iteration 1:**
$$\\nabla L(4.0) = 2(4.0) = 8.0$$
$$w_1 = 4.0 - (0.1 \\times 8.0) = 4.0 - 0.8 = 3.2$$

**Iteration 2:**
$$\\nabla L(3.2) = 2(3.2) = 6.4$$
$$w_2 = 3.2 - (0.1 \\times 6.4) = 3.2 - 0.64 = 2.56$$

Notice how $w$ steadily approaches the true minimum at $w^* = 0.0$. In larger datasets, we use Mini-batch or Stochastic Gradient Descent to accelerate updates [cit-2].`,
    citations: ['cit-1', 'cit-2'],
    quizQuestion: {
      id: 'chk-1',
      question: 'Quick check: What happens if the learning rate η is chosen excessively large?',
      options: [
        'It reaches the global minimum in fewer steps',
        'The parameter updates oscillate wildly and diverge away from the minimum',
        'The gradient automatically decays to zero',
        'The loss function permanently transforms into a linear line'
      ],
      correctIndex: 1,
      explanation: 'When η is too large, the step overshoots the valley bottom and lands on an even higher point on the opposing slope, causing the loss to explode.'
    }
  }
];

export const tutorModes = [
  { id: 'Learn', label: 'Learn', icon: 'BookOpen', description: 'Intuitive explanations, analogies, and structured teaching.' },
  { id: 'Socratic', label: 'Socratic', icon: 'HelpCircle', description: 'Guided hints and questions encouraging you to reason.' },
  { id: 'Exam prep', label: 'Exam prep', icon: 'Award', description: 'High-yield formulas, exam traps, and tricky edge cases.' },
  { id: 'Practice', label: 'Practice', icon: 'Code', description: 'Step-by-step problem exercises with progressive difficulty.' },
  { id: 'Research', label: 'Research', icon: 'Layers', description: 'Synthesize across multiple papers and compare claims.' },
  { id: 'Quick answer', label: 'Quick answer', icon: 'Zap', description: 'Concise, source-grounded answers without extra fluff.' }
];

export const mockStudyGuide = {
  title: 'Comprehensive Study Guide: Optimization & Backpropagation',
  lastUpdated: 'Today at 10:15 AM',
  sections: [
    {
      id: 'sec-overview',
      title: '1. Executive Overview',
      content: 'Optimization is the computational engine of machine learning. Rather than solving for closed-form matrix inverses which cost O(d^3), iterative first-order methods leverage gradient evaluations to navigate complex, non-convex empirical risk surfaces.'
    },
    {
      id: 'sec-concepts',
      title: '2. Core Principles & Architecture',
      items: [
        { term: 'Loss Surface Geometry', desc: 'High-dimensional loss landscapes feature local minima, saddle points, and ravines. In deep networks, saddle points surrounded by flat plateaus represent the primary impediment to convergence rather than poor local minima.' },
        { term: 'Learning Rate Dynamics', desc: 'Governs convergence stability. High rates cause divergence; excessively low rates get trapped in saddle points or require prohibitive iterations.' },
        { term: 'Batch vs Stochastic vs Mini-Batch', desc: 'Batch uses N examples (true gradient, slow). SGD uses 1 example (noisy, fast, helps escape saddles). Mini-batch uses 32-512 examples (optimal GPU vectorization).' }
      ]
    },
    {
      id: 'sec-equations',
      title: '3. Essential Mathematical Equations',
      equations: [
        { name: 'Standard Gradient Descent Update', eq: 'w_{t+1} = w_t - \\eta \\cdot \\nabla L(w_t)' },
        { name: 'Polyak Momentum Update', eq: 'v_{t+1} = \\gamma v_t + \\eta \\nabla L(w_t), \\quad w_{t+1} = w_t - v_{t+1}' },
        { name: 'Multivariate Chain Rule for Backpropagation', eq: '\\frac{\\partial L}{\\partial w_{ij}^{(l)}} = \\delta_i^{(l)} \\cdot a_j^{(l-1)}' }
      ]
    },
    {
      id: 'sec-misconceptions',
      title: '4. Common Pitfalls & Misconceptions',
      misconceptions: [
        { pitfall: 'Misconception: Gradient descent always finds the absolute global minimum.', reality: 'Correction: For non-convex deep networks, it guarantees only convergence to a stationary point (where gradient norm is approximately zero).' },
        { pitfall: 'Misconception: A larger batch size always results in better generalization.', reality: 'Correction: Overly large batch sizes tend to converge to sharp local minima that generalize poorly on unseen test data compared to smaller mini-batches.' }
      ]
    },
    {
      id: 'sec-checklist',
      title: '5. Exam Readiness Checklist',
      checklist: [
        'Can you compute the gradient of Mean Squared Error with respect to weight matrix W by hand?',
        'Do you understand why momentum prevents zig-zagging in ill-conditioned ravines?',
        'Can you explain the difference between Adam and RMSProp in terms of second moment estimation?',
        'Do you know how learning rate warmup prevents early divergence in Transformers?'
      ]
    }
  ]
};

export const mockFlashcards = [
  {
    id: 'fc-1',
    front: 'What is the physical interpretation of the gradient vector ∇L(w)?',
    back: 'The gradient vector points in the direction of greatest rate of increase (steepest ascent) of the scalar function L. Its magnitude gives the slope in that direction. Therefore, -∇L(w) points in the direction of steepest descent.',
    subject: 'Optimization',
    difficulty: 'Medium',
    status: 'learning'
  },
  {
    id: 'fc-2',
    front: 'Why does standard Mini-batch SGD often outperform Batch Gradient Descent on deep neural networks?',
    back: '1. Computationally much faster per iteration.\n2. Inherent gradient noise from random mini-batch sampling acts as implicit regularization and helps the optimizer bounce out of shallow saddle points.',
    subject: 'Optimization',
    difficulty: 'Hard',
    status: 'learning'
  },
  {
    id: 'fc-3',
    front: 'What is the role of the Momentum hyperparameter (γ ≈ 0.9)?',
    back: 'Momentum accumulates an exponentially decaying moving average of past gradients: v_{t+1} = γ v_t + η ∇L. It accelerates updates along consistent directions while dampening oscillations along high-curvature transverse directions.',
    subject: 'Algorithms',
    difficulty: 'Medium',
    status: 'review'
  },
  {
    id: 'fc-4',
    front: 'Define the Vanishing Gradient problem and its primary mathematical cause.',
    back: 'Occurs in deep architectures when backpropagated error gradients become exponentially small as they pass through saturating non-linearities (like Sigmoid or Tanh) whose derivatives are < 0.25, preventing early layers from updating.',
    subject: 'Backprop',
    difficulty: 'Hard',
    status: 'mastered'
  },
  {
    id: 'fc-5',
    front: 'How does L2 Regularization (Weight Decay) affect the gradient descent update step?',
    back: 'Adds λ/2 ||w||^2 to loss. The update becomes w_{t+1} = (1 - ηλ)w_t - η ∇L_data. The parameter w is exponentially shrunk by (1 - ηλ) at every single step, penalizing overly large weights.',
    subject: 'Regularization',
    difficulty: 'Medium',
    status: 'learning'
  }
];

export const mockQuizQuestions = [
  {
    id: 'q-1',
    question: 'In a 2D loss surface with an ill-conditioned ravine (steep in one axis, shallow in the other), standard Gradient Descent without momentum tends to:',
    options: [
      'Converge instantly along the shallow axis',
      'Oscillate wildly across the steep walls while making agonizingly slow progress along the valley floor',
      'Automatically rescale its step size using the Hessian matrix',
      'Collapse into a saddle point immediately'
    ],
    correctIndex: 1,
    explanation: 'Because the gradient is dominated by the steep orthogonal slope, updates bounce back and forth across the ravine walls rather than proceeding down the gentle slope.'
  },
  {
    id: 'q-2',
    question: 'Which of the following is TRUE regarding learning rate decay schedules (e.g., Cosine Annealing)?',
    options: [
      'It increases step size as training progresses to escape valleys',
      'It keeps the learning rate strictly constant throughout the entire epoch count',
      'It allows large exploratory steps early on, then shrinks steps to settle finely into deep local minima',
      'It is only useful for convex quadratic functions'
    ],
    correctIndex: 2,
    explanation: 'High initial learning rates explore broad basins of attraction, while decaying rates allow precision convergence without jittering out of the minimum.'
  },
  {
    id: 'q-3',
    question: 'Why are saddle points considered a larger impediment than local minima in high-dimensional non-convex neural net loss functions?',
    options: [
      'In high dimensions, almost all critical points where ∇L = 0 have both positive and negative eigenvalues in their Hessian',
      'Saddle points have infinite curvature in all directions',
      'The learning rate becomes negative at saddle points',
      'Backpropagation cannot compute derivatives when Hessian determinants are zero'
    ],
    correctIndex: 0,
    explanation: 'Dauphin et al. (2014) showed that as dimensionality increases, the probability of finding a true local minimum shrinks exponentially; the vast majority of critical points are saddle points with escape paths.'
  }
];

export const mockLearnerProfile = {
  studentName: 'Alex Chen',
  program: 'M.S. Computer Science / AI Focus',
  overallMastery: 74,
  learningPace: 'Accelerated',
  preferredStyle: 'Geometric analogies followed by formal mathematical derivations with Python/NumPy worked code snippets.',
  concepts: [
    { name: 'Linear Regression & Normal Equations', mastery: 94, status: 'Mastered', lastReviewed: '2 days ago' },
    { name: 'Loss Surfaces & Convexity', mastery: 86, status: 'Strong', lastReviewed: 'Yesterday' },
    { name: 'Gradient Descent & Variants', mastery: 72, status: 'Developing', lastReviewed: 'Today' },
    { name: 'Backpropagation & Computational Graphs', mastery: 58, status: 'Needs practice', lastReviewed: '3 days ago' },
    { name: 'L1/L2 Regularization Dynamics', mastery: 45, status: 'Needs practice', lastReviewed: '5 days ago' },
    { name: 'Batch Normalization Internals', mastery: 24, status: 'Unstudied', lastReviewed: 'Never' }
  ],
  rememberedPreferences: [
    'Prefers multi-step derivations with clear variable definitions',
    'Likes short check-for-understanding quizzes after new explanations',
    'Comfortable with linear algebra and multivariable calculus',
    'Requested focus on exam-style questions for upcoming midterms'
  ],
  struggledMisconceptions: [
    {
      topic: 'Momentum Vector Accumulation',
      detail: 'Initially thought momentum simply multiplied the current gradient rather than maintaining an exponential moving average vector.'
    },
    {
      topic: 'Batch Size Generalization Gap',
      detail: 'Assumed huge batch sizes (e.g. 8192) always yield superior test accuracy due to lower gradient variance.'
    }
  ]
};

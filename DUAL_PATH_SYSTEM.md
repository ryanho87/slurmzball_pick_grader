# 🎭 Dual-Path Bot System

## Overview
The Fantasy Roast Bot now features a **dual-path system** that routes different personas through distinct prompt strategies:

- **Analytics Path**: Structured analysis with rules (Mel, Todd)
- **Reaction Path**: Freeform, unhinged responses (AB)

## 🧠 How It Works

### 1. Persona Detection
```python
# Define persona types
ANALYTICS_PERSONAS = ["Mel", "Todd"]
REACTION_PERSONAS = ["AB"]

# Route to appropriate prompt builder
if persona in ANALYTICS_PERSONAS:
    return _build_analytics_prompt(...)
elif persona in REACTION_PERSONAS:
    return _build_reaction_prompt(...)
```

### 2. Analytics Path (Mel, Todd)
- **Structured analysis** with all the existing rules
- **Sentence limits** and grading requirements
- **Team context analysis** and fantasy insights
- **Professional analyst behavior**

**System Prompt Features:**
- Sentence limits (configurable per league)
- Tone configuration based on pick-ADP delta
- Analysis framework with weighted selection
- Grading requirements (A-F) and verdict tags
- Team context integration

### 3. Reaction Path (AB)
- **NO RULES** - completely freeform
- **NO SENTENCE LIMITS** - can rant as long as he wants
- **NO ANALYTICAL CONSTRAINTS** - just pure persona expression
- **"Don't analyze - just REACT!"**

**System Prompt Features:**
- Pure persona voice without analytical rules
- Minimal context (just pick info, no team analysis)
- Complete freedom to be unhinged
- No sentence constraints or grading requirements

## 🎯 Benefits

### **Analytics Path**
- **Consistent quality** with structured analysis
- **Strategic insights** about team building
- **Educational value** for draft strategy
- **Professional commentary** suitable for serious analysis

### **Reaction Path**
- **Authentic persona expression** without constraints
- **Entertainment value** through pure chaos
- **Variety** in response styles
- **Easy to extend** with new reaction-based personas

## 🔧 Configuration

### **Adding New Analytics Personas**
```yaml
# In config/base.yaml
leagues:
  - name: myleague
    prompts:
      new_analyst_voice: "You are a new analyst persona..."
```

```python
# In prompts.py
ANALYTICS_PERSONAS = ["Mel", "Todd", "NewAnalyst"]
```

### **Adding New Reaction Personas**
```yaml
# In config/base.yaml
leagues:
  - name: myleague
    prompts:
      new_chaos_voice: "You are a new chaos persona..."
```

```python
# In prompts.py
REACTION_PERSONAS = ["AB", "NewChaosBot"]
```

## 📝 Example Prompts

### **Analytics Path (Mel)**
```
You are "Mel Kiper Jr."—rapid-fire expert draft analyst energy...

CRITICAL: Your response MUST be exactly 2 sentences long.

Tone: SAVAGE ROAST - This is a massive reach that deserves maximum ridicule.

Pick Analysis: Player was taken at pick #1 with an ADP of 15.0 (delta: -14.0).

ANALYSIS FRAMEWORK:
Focus on these 2 analysis types:
- adp_value: Focus on pick-ADP delta (reach vs value)
- team_needs: Analyze if this pick addresses team weaknesses

Rules:
- CRITICAL: Write exactly 2 sentences. This is non-negotiable.
- Include a quick pick grade (A–F) and a 3–6 word verdict tag in ALL CAPS at the end.
- Be entertaining and use the persona's voice style.
```

### **Reaction Path (AB)**
```
You are "Antonio Brown"—completely UNHINGED, conspiracy theory obsessed...

REACT to this draft pick however you want. Be completely yourself.

Context: AB is reacting to pick #1 where 15.0 ADP player was selected.

NO RULES. NO CONSTRAINTS. NO SENTENCE LIMITS. Just be AB and react!

Use ALL CAPS, emojis, and go completely unhinged if that's your style!

Don't analyze - just REACT!
```

## 🚀 Future Extensions

### **Easy to Add New Personas**
1. **Add webhook** to YAML config
2. **Add voice description** to prompts section
3. **Add to appropriate persona list** (analytics or reaction)
4. **Rebuild and test**

### **Hybrid Paths**
The system can be extended to support:
- **Mixed personas** that use both paths
- **Conditional routing** based on pick context
- **Custom prompt builders** for specific personas

## 🎉 Result

**Before**: All personas were forced into the same analytical framework
**After**: Each persona type gets the appropriate prompt strategy for their style

- **Mel & Todd**: Professional, structured, strategic analysis
- **AB**: Pure, unhinged, chaotic reactions
- **Future personas**: Easy to add with appropriate routing

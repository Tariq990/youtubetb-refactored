"""
YouTube SEO Analysis for Generated Tags
Analyzes tags based on YouTube's ranking factors
"""

def analyze_tags_seo(tags_string):
    """
    Analyze tags from YouTube SEO perspective
    """
    
    tags = [tag.strip() for tag in tags_string.split(',')]
    
    print("=" * 80)
    print("🎯 YouTube SEO Analysis for Tags")
    print("=" * 80)
    
    # 1. SEARCH VOLUME POTENTIAL
    print("\n📊 1. SEARCH VOLUME POTENTIAL")
    print("-" * 80)
    
    # High-volume generic tags (broad appeal)
    high_volume = [t for t in tags if t in [
        'book summary', 'audiobook', 'self improvement', 'self help',
        'motivation', 'productivity', 'psychology', 'success',
        'personal development', 'book review', 'bestseller'
    ]]
    
    # Medium-volume niche tags (targeted)
    medium_volume = [t for t in tags if any(word in t for word in [
        'habits', 'mindset', 'growth', 'entrepreneur', 'booktok',
        'trending', 'student', 'reader', 'lesson'
    ]) and t not in high_volume]
    
    # Low-volume long-tail (specific, high conversion)
    long_tail = [t for t in tags if len(t.split()) >= 3 and t not in high_volume]
    
    print(f"   ✅ High-volume tags: {len(high_volume)}/44 ({len(high_volume)/44*100:.0f}%)")
    print(f"      Examples: {', '.join(high_volume[:5])}")
    print(f"   ⚡ Medium-volume tags: {len(medium_volume)}/44 ({len(medium_volume)/44*100:.0f}%)")
    print(f"      Examples: {', '.join(medium_volume[:5]) if medium_volume else 'None'}")
    print(f"   🎯 Long-tail tags: {len(long_tail)}/44 ({len(long_tail)/44*100:.0f}%)")
    print(f"      Examples: {', '.join(long_tail[:3]) if long_tail else 'None'}")
    
    # SEO Score for search volume
    volume_score = 0
    if len(high_volume) >= 8:
        volume_score += 30  # Good generic coverage
    elif len(high_volume) >= 5:
        volume_score += 20
    else:
        volume_score += 10
    
    if len(long_tail) >= 8:
        volume_score += 20  # Good long-tail coverage
    elif len(long_tail) >= 5:
        volume_score += 15
    else:
        volume_score += 5
    
    print(f"\n   📈 Search Volume Score: {volume_score}/50")
    
    # 2. KEYWORD RELEVANCE
    print("\n🎯 2. KEYWORD RELEVANCE & SPECIFICITY")
    print("-" * 80)
    
    # Check for book-specific tags
    book_specific = [t for t in tags if 'atomic habits' in t or 'james clear' in t]
    
    # Check for topic-specific tags
    topic_specific = [t for t in tags if any(word in t for word in [
        'habit', 'tiny', 'percent', 'stacking', 'loop', 'formation'
    ])]
    
    print(f"   ✅ Book-specific tags: {len(book_specific)}/44 ({len(book_specific)/44*100:.0f}%)")
    print(f"      {', '.join(book_specific[:5])}")
    print(f"   ✅ Topic-specific tags: {len(topic_specific)}/44 ({len(topic_specific)/44*100:.0f}%)")
    print(f"      {', '.join(topic_specific[:5])}")
    
    relevance_score = min(50, (len(book_specific) + len(topic_specific)) * 3)
    print(f"\n   📈 Relevance Score: {relevance_score}/50")
    
    # 3. TAG LENGTH DISTRIBUTION
    print("\n📏 3. TAG LENGTH DISTRIBUTION")
    print("-" * 80)
    
    short_tags = [t for t in tags if len(t.split()) == 1]
    medium_tags = [t for t in tags if len(t.split()) == 2]
    long_tags = [t for t in tags if len(t.split()) >= 3]
    
    print(f"   • 1-word tags: {len(short_tags)}/44 ({len(short_tags)/44*100:.0f}%)")
    print(f"     Examples: {', '.join(short_tags[:5])}")
    print(f"   • 2-word tags: {len(medium_tags)}/44 ({len(medium_tags)/44*100:.0f}%)")
    print(f"     Examples: {', '.join(medium_tags[:5])}")
    print(f"   • 3+ word tags: {len(long_tags)}/44 ({len(long_tags)/44*100:.0f}%)")
    print(f"     Examples: {', '.join(long_tags[:3])}")
    
    # Ideal distribution: 20% short, 50% medium, 30% long
    distribution_score = 0
    if 15 <= len(short_tags) <= 25:  # ~20% = 9 tags
        distribution_score += 10
    if 20 <= len(medium_tags) <= 30:  # ~50% = 22 tags
        distribution_score += 20
    if 10 <= len(long_tags) <= 20:   # ~30% = 13 tags
        distribution_score += 20
    
    print(f"\n   📈 Distribution Score: {distribution_score}/50")
    
    # 4. COMPETITION ANALYSIS
    print("\n⚔️ 4. COMPETITION LEVEL")
    print("-" * 80)
    
    # High competition (everyone uses these)
    high_comp = [t for t in tags if t in [
        'motivation', 'success', 'productivity', 'book summary',
        'self help', 'audiobook', 'bestseller'
    ]]
    
    # Low competition (specific, less saturated)
    low_comp = [t for t in tags if any(phrase in t for phrase in [
        'habit stacking', '1 percent', 'tiny changes', 'habit loop',
        'james clear atomic', 'improve daily'
    ])]
    
    print(f"   ⚠️ High-competition tags: {len(high_comp)}/44")
    print(f"      {', '.join(high_comp[:5])}")
    print(f"   ✅ Low-competition tags: {len(low_comp)}/44")
    print(f"      {', '.join(low_comp[:5]) if low_comp else 'None'}")
    
    # Balance is key: 60% high-comp, 40% low-comp
    comp_score = 0
    if len(low_comp) >= 15:  # Good unique tag coverage
        comp_score += 30
    elif len(low_comp) >= 10:
        comp_score += 20
    else:
        comp_score += 10
    
    print(f"\n   📈 Competition Balance Score: {comp_score}/30")
    
    # 5. VIRAL POTENTIAL
    print("\n🔥 5. VIRAL & TRENDING TAGS")
    print("-" * 80)
    
    viral_tags = [t for t in tags if any(word in t for word in [
        'booktok', 'trending', 'viral', 'must read', 'top books',
        'bestseller'
    ])]
    
    print(f"   🔥 Viral tags found: {len(viral_tags)}/44")
    print(f"      {', '.join(viral_tags) if viral_tags else 'None'}")
    
    viral_score = min(20, len(viral_tags) * 4)
    print(f"\n   📈 Viral Potential Score: {viral_score}/20")
    
    # 6. AUDIENCE TARGETING
    print("\n👥 6. AUDIENCE TARGETING")
    print("-" * 80)
    
    audience_tags = [t for t in tags if any(word in t for word in [
        'student', 'entrepreneur', 'reader', 'learner', 'professional',
        'book lover'
    ])]
    
    print(f"   👥 Audience tags: {len(audience_tags)}/44")
    print(f"      {', '.join(audience_tags) if audience_tags else 'None'}")
    
    audience_score = min(20, len(audience_tags) * 3)
    print(f"\n   📈 Audience Score: {audience_score}/20")
    
    # 7. SEARCHABILITY
    print("\n🔍 7. SEARCHABILITY (Natural Search Phrases)")
    print("-" * 80)
    
    search_phrases = [t for t in tags if any(phrase in t for phrase in [
        'how to', 'best', 'tips', 'guide', 'explained', 'learn',
        'improve', 'better', 'change your'
    ])]
    
    print(f"   🔍 Natural search phrases: {len(search_phrases)}/44")
    print(f"      {', '.join(search_phrases) if search_phrases else 'None'}")
    
    search_score = min(30, len(search_phrases) * 4)
    print(f"\n   📈 Searchability Score: {search_score}/30")
    
    # FINAL SCORE CALCULATION
    print("\n" + "=" * 80)
    print("🎯 FINAL SEO SCORE")
    print("=" * 80)
    
    total_score = (
        volume_score +      # 50 points
        relevance_score +   # 50 points
        distribution_score + # 50 points
        comp_score +        # 30 points
        viral_score +       # 20 points
        audience_score +    # 20 points
        search_score        # 30 points
    )
    max_score = 250
    percentage = (total_score / max_score) * 100
    
    print(f"\n   Search Volume:     {volume_score}/50")
    print(f"   Relevance:         {relevance_score}/50")
    print(f"   Distribution:      {distribution_score}/50")
    print(f"   Competition:       {comp_score}/30")
    print(f"   Viral Potential:   {viral_score}/20")
    print(f"   Audience:          {audience_score}/20")
    print(f"   Searchability:     {search_score}/30")
    print(f"   " + "-" * 40)
    print(f"   TOTAL:             {total_score}/{max_score} ({percentage:.0f}%)")
    
    # GRADE
    if percentage >= 85:
        grade = "A+ (Excellent SEO)"
    elif percentage >= 75:
        grade = "A (Very Good SEO)"
    elif percentage >= 65:
        grade = "B (Good SEO)"
    elif percentage >= 55:
        grade = "C (Acceptable SEO)"
    else:
        grade = "D (Needs Improvement)"
    
    print(f"\n   🏆 SEO GRADE: {grade}")
    
    # RECOMMENDATIONS
    print("\n" + "=" * 80)
    print("💡 SEO RECOMMENDATIONS")
    print("=" * 80)
    
    recommendations = []
    
    if len(long_tail) < 8:
        recommendations.append("⚠️ Add more long-tail tags (3-4 word phrases) for targeted traffic")
    
    if len(low_comp) < 12:
        recommendations.append("⚠️ Add more unique/specific tags to reduce competition")
    
    if len(search_phrases) < 6:
        recommendations.append("⚠️ Add natural search phrases ('how to build habits', 'best productivity books')")
    
    if len(viral_tags) < 5:
        recommendations.append("⚠️ Add more viral/trending tags (booktok, trending books, etc.)")
    
    if len(audience_tags) < 5:
        recommendations.append("⚠️ Add more audience-specific tags (students, entrepreneurs, etc.)")
    
    if not recommendations:
        recommendations.append("✅ Tag distribution is excellent! No major improvements needed.")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    # Test with IMPROVED prompt - First 40 tags only (simulating auto-trim)
    tags = """audiobook, book summary, atomic habits, james clear, atomic habits review, atomic habits summary, james clear books, atomic habits pdf, habit stacking, identity based habits, cue craving response, 4 laws behavior change, atomic habits book, atomic habits explained, atomic habits principles, how to build habits, best self help books, what is habit stacking, atomic habits key lessons, atomic habits framework, build better habits, break bad habits, tiny changes remarkable results, law of least effort, two minute rule, habit tracking, motivation, psychology, success, productivity, habits, mindset, finance, booktok, trending books, must read, bestseller, book review, viral book, readers"""
    
    analyze_tags_seo(tags)

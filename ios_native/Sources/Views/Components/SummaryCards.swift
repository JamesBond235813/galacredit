import SwiftUI

struct SummaryCardsView: View {
    let cards: [SummaryCardContent]

    var body: some View {
        HStack(spacing: 12) {
            ForEach(cards, id: \.title) { card in
                VStack(alignment: .leading, spacing: 6) {
                    Text(card.title)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundStyle(AppTheme.muted)
                    Text(card.value)
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                        .foregroundStyle(AppTheme.text)
                        .lineLimit(1)
                        .minimumScaleFactor(0.72)
                    Text(card.subtitle)
                        .font(.system(size: 11, weight: .medium))
                        .foregroundStyle(AppTheme.muted)
                        .lineLimit(2)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .frame(maxWidth: .infinity, alignment: .topLeading)
                .glassCard()
            }
        }
    }
}

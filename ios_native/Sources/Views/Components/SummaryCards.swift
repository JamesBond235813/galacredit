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
                    AdaptiveSummaryValueText(value: card.value)
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

private struct AdaptiveSummaryValueText: View {
    let value: String

    var body: some View {
        ViewThatFits(in: .horizontal) {
            valueText(size: 26)
            valueText(size: 22)
            valueText(size: 18)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func valueText(size: CGFloat) -> some View {
        Text(value)
            .font(.system(size: size, weight: .bold, design: .rounded))
            .foregroundStyle(AppTheme.text)
            .monospacedDigit()
            .lineLimit(1)
            .minimumScaleFactor(0.48)
            .allowsTightening(true)
    }
}

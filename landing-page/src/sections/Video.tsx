import type { Section as PageSection } from '../types';
import { Media } from '../components/Media';
import { Reveal, Section, SectionHeader } from '../components/ui';
import { FeatureGrid } from './Features';

export function Video({ section }: { section: PageSection }) {
  return (
    <Section section={section}>
      <SectionHeader section={section} align="center" />
      <Reveal className="mx-auto mt-12 max-w-[1100px] lg:mt-14">
        <Media media={{ type: 'video', frame: 'plain', ...section.video }} />
      </Reveal>
      {section.items?.length ? <FeatureGrid items={section.items} count={section.columns} /> : null}
    </Section>
  );
}

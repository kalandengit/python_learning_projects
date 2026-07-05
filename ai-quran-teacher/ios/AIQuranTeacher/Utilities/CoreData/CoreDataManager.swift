import CoreData
import Foundation

/// Owns the Core Data stack backing offline mode.
///
/// The `AIQuranTeacher.xcdatamodeld` model defines:
///   SurahEntity, AyahEntity, BookmarkEntity, ProgressEntity,
///   RecitationSessionEntity, TajweedMistakeEntity
/// with SurahEntity 1-to-many AyahEntity.
final class CoreDataManager {
    static let shared = CoreDataManager()

    let container: NSPersistentContainer

    var viewContext: NSManagedObjectContext { container.viewContext }

    init(inMemory: Bool = false) {
        container = NSPersistentContainer(name: "AIQuranTeacher")
        if inMemory {
            container.persistentStoreDescriptions.first?.url = URL(fileURLWithPath: "/dev/null")
        }
        container.loadPersistentStores { _, error in
            if let error {
                // Surfacing this loudly during development; production builds
                // should fall back to a fresh store and report to telemetry.
                fatalError("Failed to load Core Data store: \(error)")
            }
        }
        container.viewContext.automaticallyMergesChangesFromParent = true
    }

    func save() {
        let context = viewContext
        guard context.hasChanges else { return }
        do {
            try context.save()
        } catch {
            context.rollback()
            print("Core Data save failed: \(error)")
        }
    }

    // MARK: - Bookmarks

    func toggleBookmark(ayahId: Int) {
        let request = NSFetchRequest<NSManagedObject>(entityName: "BookmarkEntity")
        request.predicate = NSPredicate(format: "ayahId == %d", ayahId)
        if let existing = (try? viewContext.fetch(request))?.first {
            viewContext.delete(existing)
        } else {
            let bookmark = NSEntityDescription.insertNewObject(
                forEntityName: "BookmarkEntity", into: viewContext
            )
            bookmark.setValue(ayahId, forKey: "ayahId")
            bookmark.setValue(Date(), forKey: "createdAt")
        }
        save()
    }

    func bookmarkedAyahIds() -> Set<Int> {
        let request = NSFetchRequest<NSManagedObject>(entityName: "BookmarkEntity")
        let results = (try? viewContext.fetch(request)) ?? []
        return Set(results.compactMap { $0.value(forKey: "ayahId") as? Int })
    }

    // MARK: - Progress

    func recordSession(ayahId: Int, accuracy: Double, mistakes: [TajweedMistake]) {
        let session = NSEntityDescription.insertNewObject(
            forEntityName: "RecitationSessionEntity", into: viewContext
        )
        session.setValue(UUID(), forKey: "id")
        session.setValue(ayahId, forKey: "ayahId")
        session.setValue(accuracy, forKey: "accuracy")
        session.setValue(Date(), forKey: "recordedAt")

        for mistake in mistakes {
            let entity = NSEntityDescription.insertNewObject(
                forEntityName: "TajweedMistakeEntity", into: viewContext
            )
            entity.setValue(mistake.type.rawValue, forKey: "type")
            entity.setValue(mistake.severity.rawValue, forKey: "severity")
            entity.setValue(mistake.wordIndex, forKey: "wordIndex")
            entity.setValue(mistake.expectedWord, forKey: "expectedWord")
            entity.setValue(mistake.actualWord, forKey: "actualWord")
            entity.setValue(mistake.suggestion, forKey: "suggestion")
            entity.setValue(session, forKey: "session")
        }
        save()
    }
}

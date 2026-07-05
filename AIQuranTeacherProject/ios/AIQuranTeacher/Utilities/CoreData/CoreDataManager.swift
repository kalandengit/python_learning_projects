import CoreData

/// Lightweight Core Data wrapper plus the persistence helpers referenced by the
/// view models (reading progress, bookmarks). The bookmark/last-read helpers
/// are scaffolds backed by `UserDefaults` until the Core Data model is added.
final class CoreDataManager {
    static let shared = CoreDataManager()
    private init() {}

    lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "AIQuranTeacher")
        container.loadPersistentStores { _, error in
            if let error = error as NSError? {
                fatalError("Unresolved error \(error), \(error.userInfo)")
            }
        }
        return container
    }()

    var context: NSManagedObjectContext {
        persistentContainer.viewContext
    }

    func saveContext() {
        guard context.hasChanges else { return }
        do {
            try context.save()
        } catch {
            let nserror = error as NSError
            fatalError("Unresolved error \(nserror), \(nserror.userInfo)")
        }
    }

    // MARK: - Reading progress / bookmarks (scaffold)

    private let bookmarksKey = "bookmarkedAyahs"

    func getLastReadSurah() -> Surah? {
        // TODO: restore the last-read surah from Core Data.
        nil
    }

    func getBookmarkedAyahs() -> Set<Int> {
        let ids = UserDefaults.standard.array(forKey: bookmarksKey) as? [Int] ?? []
        return Set(ids)
    }

    func toggleBookmark(ayahId: Int) {
        var ids = getBookmarkedAyahs()
        if ids.contains(ayahId) { ids.remove(ayahId) } else { ids.insert(ayahId) }
        UserDefaults.standard.set(Array(ids), forKey: bookmarksKey)
    }
}
